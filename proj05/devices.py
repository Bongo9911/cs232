'''Devices that interact with the CPU: I/O ports, timer, etc.'''

import threading
import time

class TimerController(threading.Thread):
    '''This controller controls a timer device that interrupts the
    CPU whenever the timer runs down to 0.  A countdown value of -1
    means the timer is not running.
    '''
    import cpu
    DELAY = cpu.DELAY_BETWEEN_INSTRUCTIONS
    NOT_RUNNING = -1

    def __init__(self, cpu, dev_id, debug=False):
        threading.Thread.__init__(self)
        self._cpu = cpu

        # Bus address identifier: used to indicate to the CPU
        # what device has raised an interrupt.
        self._dev_id = dev_id
        self._countdown = self.NOT_RUNNING
        # mutex lock to protect setting/getting the countdown.
        self._mutex = threading.Lock()

        self._debug = debug
        if self._debug: print("TimerController created!")

    def set_countdown(self, val):
        '''Set the number of cycles until the timer fires.
        '''
        with self._mutex:
            self._countdown = val
        if self._debug: print("Timer: set countdown to", self._countdown)

    def set_debug(self, debug):
        self._debug = debug

    def run(self):
        '''When running, count down from _countdown to 0, and then
        raise an interrupt.  When not running, periodically see if
        the countdown value has been set -- enabling the timer again.
        countdown value of -1 indicates the timer is not running.
        '''

        if self._debug: print("TimerController: running!")
        while True:
            # Copy value to local variable
            with self._mutex:
                countdown = self._countdown
                
            if countdown > 0:
                countdown -= 1
            if countdown == 0:
                # timer expired!
                self._cpu.take_interrupt_mutex()
                self._cpu.add_interrupt_addr(self._dev_id)
                self._cpu.set_interrupt(True)
                self._cpu.release_interrupt_mutex()
                # Don't generate another interrupt until the
                # previous one is handled and the interrupt is
                # reset.
                countdown = self.NOT_RUNNING
            else:    # countdown < 0: indicating do nothing.
                pass

            with self._mutex:
                self._countdown = countdown

            time.sleep(self.DELAY)

