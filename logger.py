
from config import config as tconf


def log(*arg):
    if tconf.logic_print:
        print(*arg)
