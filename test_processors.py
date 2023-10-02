import time
import _thread
import gc
import machine


class Test:
    def __init__(self):
        self.dc = _thread.allocate_lock()

    def run(self):
        while True:
            dc.acquire()
            try:
                print('Running thread 1')
            except KeyboardInterrupt:
                print("\nkeyboard interrupt!")
                break
