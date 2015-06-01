import os
import pytest
import binascii
from hecate.tmux import Tmux, DeadServer
import time

muxes = []


def teardown_function(fn):
    while muxes:
        muxes.pop().shutdown()


def newmux():
    mux = Tmux(binascii.hexlify(os.urandom(8)))
    muxes.append(mux)
    return mux


def test_muxes_are_independent():
    mux1 = newmux()
    mux2 = newmux()
    mux1.a_buffer()
    assert mux1.buffers()
    assert not mux2.buffers()


def test_has_no_buffers_to_start_with():
    t = newmux()
    assert not t.buffers()


def test_can_save_data_to_a_buffer():
    t = newmux()
    data = "Hello\nworld?"
    t.new_buffer(data)
    buffers = t.buffers()
    assert len(buffers) == 1
    assert t.get_buffer(buffers[0]) == data


def test_can_set_data_to_an_existing_buffer():
    t = newmux()
    data = "To be set"
    b = t.a_buffer()
    t.set_buffer(b, data)
    assert t.get_buffer(b) == data


def test_starts_with_a_single_session():
    assert len(newmux().sessions()) == 1


def test_creates_sessions_of_desired_name():
    mux = newmux()
    mux.new_session(name="kittenbob")
    assert "kittenbob" in mux.sessions()


def test_can_capture_a_pane():
    name = "testcapturing"
    mux = newmux()
    mux.new_session(
        width=50, height=50, command="echo hello world; bash", name=name
    )
    sessions = mux.sessions()
    assert name in sessions
    assert len(sessions) == 2
    for t in mux.sessions():
        if t != name:
            mux.kill_session(t)
    panes = mux.panes()
    assert len(panes) == 1
    pane_contents = mux.capture_pane(panes[0])
    assert "hello world" in pane_contents
    assert len(pane_contents.split("\n")) == 50


def test_can_send_content_to_the_screen():
    mux = newmux()
    pane = mux.panes()[0]
    mux.send_keys(pane, ["echo", " ", "hello", " ", "world", "Enter"])
    start = time.time()
    while time.time() < start + 1:
        contents = mux.capture_pane(pane)
        assert "echo hello world\n" in contents
        if "\nhello world\n" in contents:
            break

    assert "\nhello world\n" in contents


def test_can_detect_when_server_dies():
    mux = newmux()
    mux.kill_session(mux.sessions()[0])
    with pytest.raises(DeadServer):
        mux.sessions()
