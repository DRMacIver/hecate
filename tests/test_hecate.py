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


def test_can_run_vim():
    f = tempfile.mktemp()
    with Hecate("vim") as h:
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
        print(h.screenshot())
        h.await_exit()
    with open(f) as r:
        text = r.read()
        assert "Hello world" in text
        assert "Goodbye world" not in text


def test_reports_abnormal_exit():
    with pytest.raises(AbnormalExit):
        with Hecate("cat", "/does/not/exist/no/really"):
            pass
