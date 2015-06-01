import hecate.runner as runner
from hecate.tmux import Tmux, DeadServer
import os
import sys
import time
import tempfile
import binascii
import signal
import traceback
import shlex
from warnings import warn


class HecateException(Exception):
    pass


class Timeout(HecateException):
    pass


class InvalidState(HecateException):
    pass


class AbnormalExit(HecateException):
    pass


class HecateWillHauntYou(HecateException):
    pass


def must_die(pid):
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.01)
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def hecate_temp_dir():
    target = os.path.join(
        tempfile.gettempdir(), "hecate_comms_files")
    try:
        os.mkdir(target)
    except FileExistsError:
        pass
    return target

HECATE_SESSION_NAME = "hecate_runner"

RUNNER_PROGRAM = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "runner.py"))


class Runner(object):
    """
    A Runner manages a running console app. It is started in a
    virtual terminal of a specified size. You may then interact with it and
    get screenhots of the current state of the screen. Once you are done,
    you must call shutdown on the instance. You can also use it as a context
    manager for automatic resource cleanup.
    """
    print_on_exit = False

    def __init__(
        self,
        *command,
        width=80, height=24,
        wait_interval=0.01, default_timeout=1
    ):
        """
        Hecate will run the command line arguments specified by command (
        note: These may not contain spaces. If you want to pass this to a
        shell, invoke the shell explicitly).

        Additional parameters:

            width and height specify the height of the console to run in in
                characters. Note that you cannot currently resize the console
                once started.
            wait_interval is the polling frequency for functions like
                await_text. A smaller value will be more CPU intensive but
                may be slightly faster.
            default_timeout specifies the default timeout for all await
                functions.
        """
        self.wait_interval = wait_interval
        self.default_timeout = default_timeout
        self.has_shutdown = False
        self.tmux_id = binascii.hexlify(os.urandom(8)).decode('ascii')
        self.exit_seen = False
        self.tmux = Tmux(self.tmux_id)
        try:
            self.report_file = os.path.join(
                hecate_temp_dir(), self.tmux_id
            )
            with open(self.report_file, "w"):
                pass
            self.shutdown_called = False
            self.launched = False
            self.tmux.new_session(
                width=width, height=height, name=HECATE_SESSION_NAME,
                command=' '.join(
                    map(
                        shlex.quote, [
                            sys.executable,
                            RUNNER_PROGRAM, self.report_file
                        ] + list(command)))
            )
            sessions = [
                l.strip() for l in self.tmux.execute_command(
                    "list-sessions", "-F", "#{session_name}").splitlines()
            ]
            sessions.remove(HECATE_SESSION_NAME)
            for s in sessions:
                self.tmux.kill_session(s)
            windows = [
                l.strip() for l in self.tmux.execute_command(
                    "list-windows", "-F", "#{window_name}").splitlines()
            ]
            assert len(windows) == 1
            self.target_window = windows[0]
            assert len(self.tmux.panes()) == 1
            self.screenshot()
            for _ in self.poll_until_timeout(self.default_timeout):
                report = self.report_variables()
                if runner.CHILD in report:
                    self.ready = True
                    self.screenshot()
                    break
            else:
                raise Timeout(
                    "Process failed to start"
                )
            report = self.report_variables()
            os.kill(report[runner.CONTROLLER], signal.SIGUSR1)
            self.child_pid = report[runner.CHILD]
        except:
            self.shutdown_called = True
            self.tmux.shutdown()
            raise

    def shutdown(self):
        """
        Kill this Hecate instance and free all resources associated with it.

        This is safe to call multiple times but is a no-op the second time. It
        will be automatically called if you are using this as a context
        manager.
        """
        if self.shutdown_called:
            return
        self.shutdown_called = True
        try:
            if not self.exit_seen:
                try:
                    self.await_exit()
                except Timeout:
                    pass
            if self.print_on_exit:
                print(self.last_screenshot)
        finally:
            report = self.report_variables()
            for c in [runner.CHILD, runner.CONTROLLER]:
                try:
                    must_die(report[c])
                except KeyError:
                    pass
                except:
                    traceback.print_exc()
            self.tmux.shutdown()

    def __del__(self):
        if not self.shutdown_called:
            warn(HecateWillHauntYou(
                "Garbage collecting Hecate instance which has not been shut "
                "down properly. This is a really bad idea. Always call "
                "shutdown on your Hecate instances, ideally by using them as "
                "context managers."))
            self.shutdown()

    def screenshot(self):
        """
        Return a string representing the current state of the screen.
        """
        try:
            result = self.tmux.capture_pane(0)
            self.last_screenshot = result
            return result
        except DeadServer:
            return self.last_screenshot

    def press(self, key):
        """
        Press the key identified by key-press. This will currently be passed
        uninterpreted to tmux, which will assign its own meaning to it. So e.g
        Enter will be the enter key, C-d will send EOF, etc.
        """
        self.tmux.send_key(0, key)

    def write(self, text):
        """
        Write this as text to the console as it is. Will not be interpreted as
        a special character, so e.g. Enter is the literal string Enter and not
        a return character.
        """
        self.tmux.new_buffer(text)
        self.tmux.execute_command("paste-buffer")

    def await_text(self, text, timeout=None):
        """
        Wait for 'text' to appear on the screen, accounting for line wrapping.
        If timeout (or default timeout if not set) seconds elapse first, raise
        a Timeout error.
        """
        for _ in self.poll_until_timeout(timeout):
            screen = self.screenshot()
            munged = screen.replace('\n', '')
            if text in munged:
                return
        raise Timeout("Timeout while waiting for text %r to appear" % (text,))

    def await_exit(self, timeout=None):
        """
        Wait for the process to exit. If it exits with a non-zero status code,
        AbnormalExit will be raised. If timeout or default_timeout seconds pass
        without it exiting, raise a Timeout.
        """
        for _ in self.poll_until_timeout(timeout):
            report = self.report_variables()
            if runner.EXIT_STATUS in report:
                self.exit_seen = True
                status = report[runner.EXIT_STATUS]
                if status != 0:
                    raise AbnormalExit(
                        "Process exited with status %d" % (status,))
                else:
                    return
        self.screenshot()
        raise Timeout("Timeout while waiting for process to exit")

    def kill(self, sig):
        """
        Send a signal to the running process. sig is either an integer signal
        number or the name of the signal.
        """
        if isinstance(sig, str):
            sig = getattr(signal, sig)
        os.kill(self.child_pid, sig)

    def poll_until_timeout(self, timeout=None):
        if timeout is None:
            timeout = self.default_timeout
        start = time.time()
        while time.time() <= start + timeout:
            yield
            time.sleep(self.wait_interval)

    def report_variables(self):
        with open(self.report_file) as r:
            result = {}
            for line in r:
                k, v = line.split(":", 2)
                result[k] = int(v)
            return result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
