from __future__ import division, print_function, absolute_import, \
    unicode_literals


import time
import sys
import os
import traceback
import signal

COMMAND_FAILED_STATUS = 111

CONTROLLER = "Controller"
CHILD = "Child"
EXIT_STATUS = "Exit status"


def print_usage_and_die():
    print(
        "Usage: runner.py report-file command...",
        file=sys.stderr
    )
    sys.exit(1)

sig_user_1 = None


def main():
    global sig_usr_1

    if len(sys.argv) <= 2:
        print_usage_and_die()
    report_file = sys.argv[1]
    if os.path.abspath(report_file) != report_file:
        print(
            "report-file must be an absolute path. Got %r" % (report_file,),
            file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(report_file):
        print(
            "No such file %r" % (report_file,),
            file=sys.stderr)
        sys.exit(1)

    command = sys.argv[2:]
    assert command

    reporter = open(report_file, "w")

    def report_field(field, value):
        reporter.write("%s: %d\n" % (field, value))
        reporter.flush()
    report_field(CONTROLLER, os.getpid())
    r, w = os.pipe()
    child = os.fork()
    sys.stdout.flush()
    if not child:
        try:
            os.close(w)
            while True:
                time.sleep(0.01)
                data = os.read(r, 1)
                if not data:
                    continue
                progress = data == b"1"
                os.close(r)
                assert progress, data
                break
            reporter.close()
            os.execvp(command[0], command)
        except:
            traceback.print_exc()
            os._exit(COMMAND_FAILED_STATUS)
    report_field(CHILD, child)
    os.close(r)

    def awaken_child(signal, frame):
        global sig_user_1
        sig_user_1 = True
        os.write(w, b"1")
        os.close(w)

    signal.signal(signal.SIGUSR1, awaken_child)
    while not sig_user_1:
        signal.pause()
    _, exit_status = os.waitpid(child, 0)
    report_field(EXIT_STATUS, exit_status)
    reporter.close()
    # Long sleep to give time to snapshot the screen
    time.sleep(1)

if __name__ == '__main__':
    main()
