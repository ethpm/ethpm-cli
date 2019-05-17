import os
import sys


def get_terminal_width() -> int:
    if sys.stdin.isatty():
        _, columns = os.popen("stty size", "r").read().split()
    else:
        columns = "100"
    return int(columns)
