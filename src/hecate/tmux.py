import subprocess
import re
from contextlib import contextmanager
import os
import tempfile


AFTER_COLON = re.compile(":.+$")


class CommandFailed(Exception):
    pass


def _extract_names(output):
    return list(filter(None, [
        AFTER_COLON.sub("", l)
        for l in output.split("\n")
    ]))


TMUX = os.getenv("HECATE_TMUX_BINARY") or "tmux"


class Tmux(object):
    def __init__(self, name):
        self.name = name
        try:
            subprocess.check_output(
                [TMUX, "-u", "-L", self.name, "list-sessions"],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError:
            self.new_session()

    def execute_command(self, *command):
        try:
            cmd = [TMUX, "-u", "-L", self.name] + list(map(str, command))
            return subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT
            ).decode('ascii')
        except subprocess.CalledProcessError as e:
            raise CommandFailed(e.output)

    def new_session(
        self, width=80, height=24, window=None, name=None, command=None
    ):
        arguments = ["new-session", "-d", "-x", width, "-y", height]
        if window is not None:
            arguments.extend([
                "-s", window
            ])
        if name is not None:
            arguments.extend(["-s", name])
        if command is not None:
            arguments.append(command)
        self.execute_command(*arguments)

    def kill_session(self, name):
        self.execute_command("kill-session", "-t", name)

    def buffers(self):
        return _extract_names(self.execute_command("list-buffers"))

    def panes(self, session=None):
        if session is None:
            return _extract_names(self.execute_command("list-panes"))
        else:
            return _extract_names(self.execute_command(
                "list-panes", "-t", session
            ))

    def select_pane(self, pane):
        self.execute_command("select-pane", "-t", pane)

    def send_keys(self, pane, keys):
        self.execute_command(*(
            ["send-keys", "-t", pane] + list(keys)
        ))

    def send_key(self, pane, key):
        self.execute_command(*(
            ["send-keys", "-t", pane, key]
        ))

    def sessions(self):
        return _extract_names(self.execute_command("list-sessions"))

    def windows(self):
        return _extract_names(self.execute_command("list-windows"))

    def set_buffer(self, buf, data):
        self.execute_command("set-buffer", "-b", buf, data)

    def get_buffer(self, buf):
        with self.temp() as t:
            self.execute_command("save-buffer", "-b", buf, t)
            with open(t, encoding="utf-8") as o:
                return o.read()

    def new_buffer(self, data):
        with self.temp() as t:
            with open(t, "w", encoding="utf-8") as o:
                o.write(data)
            self.execute_command("load-buffer", t)

    def a_buffer(self):
        buffers = self.buffers()
        if buffers:
            return buffers[0]
        self.new_buffer("a_buffer")
        buffers = self.buffers()
        assert buffers
        return buffers[0]

    def capture_pane(self, pane):
        buf = self.a_buffer()
        self.execute_command("capture-pane", "-b", buf, "-t", pane)
        return self.get_buffer(buf)

    def shutdown(self):
        try:
            o = open("/dev/null")
            subprocess.check_call(
                [TMUX, "-u", "-L", self.name, "kill-server"],
                stderr=o
            )
        except subprocess.CalledProcessError:
            pass
        finally:
            o.close()

    @contextmanager
    def temp(self):
        try:
            fd, name = tempfile.mkstemp()
            os.close(fd)
            yield name
        finally:
            try:
                os.unlink(name)
            except os.FileNotFoundError:
                pass
