import sys
import signal
import os


def trap_signal(name):
    try:
        def handle(sig, frame):
            print("Received signal %s" % (name,))
        signal.signal(getattr(signal, name), handle)
    except (OSError, ValueError):
        pass


def main():
    print(os.getpid())
    for k in vars(signal):
        if k[:3] == "SIG":
            trap_signal(k)
    sys.stdin.read()

if __name__ == '__main__':
    main()
