import time

def next_sleep():
    return (300 - time.time() % 300) + 10
