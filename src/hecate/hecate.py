import hecate.runner as runner
from hecate.tmux import Tmux
import os
import sys
import time
import tempfile
import binascii
import signal
import traceback
import shlex


class HecateException(Exception):
    pass


class Timeout(HecateException):
    pass


class InvalidState(HecateException):
    pass


class AbnormalExit(HecateException):
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


class Hecate(object):
    print_on_exit = False

    def __init__(
        self,
        *command,
        width=80, height=24,
        wait_interval=0.01, default_timeout=1
    ):
        self.wait_interval = wait_interval
        self.default_timeout = default_timeout
        self.has_shutdown = False
        self.tmux_id = binascii.hexlify(os.urandom(8)).decode('ascii')
        self.tmux = Tmux(self.tmux_id)
        try:
            self.report_file = os.path.join(
                hecate_temp_dir(), self.tmux_id
            )
            with open(self.report_file, "w"):
                pass
            self.ready = False
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
            self.started = False
            self.screenshot()
        except:
            self.tmux.shutdown()
            raise

    def screenshot(self):
        result = self.tmux.capture_pane(0)
        self.last_screenshot = result
        return result

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

    def press(self, key):
        self.tmux.send_key(0, key)

    def write(self, text):
        self.tmux.new_buffer(text)
        self.tmux.execute_command("paste-buffer")

    def await_ready(self, timeout=None):
        if self.ready:
            assert self.launched
            return
        self.launched = True
        for _ in self.poll_until_timeout(timeout):
            report = self.report_variables()
            if runner.CHILD in report:
                self.ready = True
                self.screenshot()
                return
        raise Timeout(
            "Process failed to start"
        )

    def await_text(self, text, timeout=None):
        for _ in self.poll_until_timeout(timeout):
            screen = self.screenshot()
            munged = screen.replace('\n', '')
            if text in munged:
                return
        raise Timeout("Timeout while waiting for text %r to appear" % (text,))

    def await_exit(self, timeout=None):
        for _ in self.poll_until_timeout(timeout):
            report = self.report_variables()
            if runner.EXIT_STATUS in report:
                status = report[runner.EXIT_STATUS]
                if status != 0:
                    raise AbnormalExit(
                        "Process exited with status %d" % (status,))
                else:
                    return
        self.screenshot()
        raise Timeout("Timeout while waiting for process to exit")

    def start(self, timeout=None):
        assert not self.started
        self.started = True
        self.await_ready(timeout)
        report = self.report_variables()
        os.kill(report[runner.CONTROLLER], signal.SIGUSR1)

    def shutdown(self):
        try:
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

        if not self.started:
            raise InvalidState("shutdown called on non-started instance")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
