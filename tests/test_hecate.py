# coding=utf-8

from hecate.hecate import Hecate, AbnormalExit
import tempfile
import pytest


def test_can_launch_a_simple_program():
    f = tempfile.mktemp()
    with Hecate("bash", "-c", "echo hello world > %s" % (f,)) as h:
        return
    print(h.last_screenshot)
    with open(f) as r:
        assert "Hello world" in r.read()


def test_can_kill_vim():
    with Hecate("vim") as h:
        h.await_text("VIM")
        print(h.screenshot())
        h.press(":")
        h.press("q")
        h.press("Enter")


def test_can_write_unicode():
    with Hecate("cat") as h:
        h.write("☃")
        h.await_text("☃")


def test_can_run_vim():
    f = tempfile.mktemp()
    with Hecate("/usr/bin/vim") as h:
        h.await_text("VIM")
        h.press("i")
        h.write("Hello world")
        h.press("Enter")
        h.write("Goodbye world")
        h.press("Escape")
        h.write("dd")
        h.write(":w " + f)
        h.press("Enter")
        h.write(":q")
        h.press("Enter")
        # Second enter because if running with unset environment in tox it will
        # complain that it can't write viminfo and tell you to press enter to
        # continue.
        h.press("Enter")
        print(h.screenshot())
        h.await_exit()
    with open(f) as r:
        text = r.read()
        assert "Hello world" in text
        assert "Goodbye world" not in text


def test_can_send_enter():
    with Hecate("cat") as h:
        h.write("hi")
        h.press("Enter")
        h.write("there")
        h.await_text("there")
        assert "hi\nthere" in h.screenshot()


def test_reports_abnormal_exit():
    with pytest.raises(AbnormalExit):
        with Hecate("cat", "/does/not/exist/no/really"):
            pass
