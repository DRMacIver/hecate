import os
import glob
import tempfile
import shutil

TMUX_SOURCES = glob.glob(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "muxen")) +
    "/*.tar.gz"
)

TMUX_TO_SOURCES = {
    os.path.basename(f).replace(".tar.gz", ""): f for f in TMUX_SOURCES
}

TARGET_DIR = os.path.expanduser("~/.tmuxen")


def sys(command):
    print(command)
    result = os.system(command)
    if result:
        raise ValueError("Command returned status %d" % (result,))


def main():
    try:
        os.mkdir(TARGET_DIR)
    except FileExistsError:
        pass
    for tmux, path in TMUX_TO_SOURCES.items():
        target = os.path.join(TARGET_DIR, tmux)
        if not os.path.exists(target):
            try:
                d = tempfile.mkdtemp()
                os.chdir(d)
                sys("tar -xvf %s" % (path,))
                os.chdir(os.listdir(d)[0])
                sys("./configure")
                sys("make")
                sys("mv tmux %s" % (target,))
            finally:
                shutil.rmtree(d)

if __name__ == '__main__':
    main()
