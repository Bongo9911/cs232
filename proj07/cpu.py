import time
import threading   # for Lock
from ram import MMU

MAX_CHARS_PER_ADDR = 4

# Time to delay between executing instructions, in seconds.
DELAY_BETWEEN_INSTRUCTIONS = 0.2

# Interrupt device ids
SOFTWARE_TRAP_DEV_ID = 0
TIMER_DEV_ID  = 1
# KBRD_DEV_ID   = 1
# SCREEN_DEV_ID = 2

# REASONs for software traps.
END_OF_PROGRAM = 0
ILLEGAL_INSTRUCTION = 2

class CPU:

    def __init__(self, ram, os, num=0):

        # TODO: the CPU should know nothing about the OS.  The CPU should
        # just execute instructions and handle the interrupts.  We should
        # not pass the OS object in, but instead should make an API which
        # the OS code could call to register a callback to be called for
        # the various interrupts -- the software trap, timer expiration,
        # etc.
        
        self._num = num   # unique ID of this cpu
        self._registers = {
            'reg0' : 0,
            'reg1' : 0,
            'reg2' : 0,
            'pc': 0
            }

        self._mmu = MMU(ram)
        self._os = os
        self._debug = False
        # Set _stop to True to "power down" the CPU.
        self._stop = False

        self._intr_raised = False
        self._intr_addrs = set()

        self._intr_lock = threading.Lock()

        self._intr_vector = [self._trap_isr,
                             self._timer_isr]
                             

        # Create device controller threads.
        # This is done here so that when the CPU is done running a program,
        # the screen and kbd threads can be killed.  Then if it is told
        # to start up again, it will create new threads (since you cannot
        # restart stopped threads).
        # TODO: revisit the above decision?  CPU thread is not stopped anymore...
        # Also, not using the Keyboard and Screen devices...
        # And, it seems weird for the CPU to start up the other device controllers...
        
        import devices
        self._timer = devices.TimerController(self, TIMER_DEV_ID, self._debug)

        # Start up the thread, though its countdown will be -1, so it won't do
        # anything until that is set.
        self._timer.start()

    def set_pc(self, pc):
        # TODO: check if value of pc is good?
        self._registers['pc'] = pc

    def get_num(self):
        return self._num

    def set_debug(self, debug):
        self._debug = debug
        self._timer.set_debug(debug)

    def take_interrupt_mutex(self):
        self._intr_lock.acquire()

    def release_interrupt_mutex(self):
        self._intr_lock.release()

    def set_interrupt(self, intr_val):
        '''Set the interrupt line to be True if an interrupt is raised, or
        False to indicate the interrupt is cleared.
        '''
        assert isinstance(intr_val, bool)
        self._intr_raised = intr_val

    def add_interrupt_addr(self, addr):
        '''Add the device bus address to the set of devices that have
        raised an interrupt.'''
        self._intr_addrs.add(addr)

    def get_registers(self):
        return self._registers

    def set_registers(self, registers):
        if registers == {}:
            raise ValueError
        self._registers = registers

    def isregister(self, s):
        return s in ('reg0', 'reg1', 'reg2', 'pc')

    def __str__(self):
        res = '''CPU {}: pc {}, reg0 {}, reg1 {}, reg2 {}'''.format(
            self._num, self._registers['pc'], self._registers['reg0'],
            self._registers['reg1'], self._registers['reg2'])
        return res

    def reset_timer(self, quantum):
        self._timer.set_countdown(quantum)

    def run_cpu(self):
        '''Run the CPU which repeatedly executes the instructions
        at the program counter (pc), until the "end" instruction is reached.
        Assumes the registers, including the pc, have been set for the
        "ready" process.  The execution will be interrupted by the timer
        causing a context switch to run the next process in the
        ready queue.
        '''

        while True:

            if self._stop:
                # No more processes to execute.
                break

            if self._debug:
                # print(self._registers)
                print("CPU {}: executing code at [{}]: {}".format(self._num, self._registers['pc'],
                                                          self._mmu._get_value_at(self._registers['pc'])))

            # Execute the next instruction.
            self.parse_instruction(self._mmu._get_value_at(self._registers['pc']))

            if self._debug:
                print(self)

            # Now, check if an interrupt has been raised.  If it has, run the
            # corresponding handler.  Repeat until all interrupts have been serviced.
            self.take_interrupt_mutex()
            try:
                if self._intr_raised:
                    if self._debug: print("CPU {}: got interrupt".format(self._num))

                    for addr in sorted(self._intr_addrs):
                        # Call the interrupt handler.
                        self._intr_vector[addr]()
                        # Remove the device address from the list of pending interrupts.
                        self._intr_addrs.remove(addr)
                    
                    # Mark all interrupts handled.
                    self.set_interrupt(False)  # clear the interrupt
            finally:
                self.release_interrupt_mutex()
            
            time.sleep(DELAY_BETWEEN_INSTRUCTIONS)


    def parse_instruction(self, instr):
        '''return False when program is done'''

        # Make sure it is an instruction.  The PC may have wandered into
        # data territory.
        if isinstance(instr, int):
            print("ERROR: Not an instruction: {}".format(instr))
            self._generate_trap(ILLEGAL_INSTRUCTION)
            return
            
        instr = instr.replace(",", "")
        words = instr.split()
        instr = words[0]
        if len(words) == 2:
            dst = words[1]    # for jmp and call.
        elif len(words) == 3:
            src = words[1]
            dst = words[2]

        if instr == "call":
            # Call a python function.  Syntax is
            # call fname.  Function fname is a method in 
            # CalOS class and is called with the values in reg0, reg1, and reg2.
            self.handle_call(dst)
            self._registers['pc'] += 1
        elif instr == "mov":
            self.handle_mov(src, dst)
            self._registers['pc'] += 1
        elif instr == 'add':
            self.handle_add(src, dst)
            self._registers['pc'] += 1
        elif instr == 'sub':
            self.handle_sub(src, dst)
            self._registers['pc'] += 1
        elif instr == 'jez':
            self.handle_jez(src, dst)
        elif instr == 'jnz':
            self.handle_jnz(src, dst)
        elif instr == 'jgz':
            self.handle_jgz(src, dst)
        elif instr == 'jlz':
            self.handle_jlz(src, dst)
        elif instr == 'jmp':
            self.handle_jmp(dst)
        elif instr == 'end':
            self._generate_trap(END_OF_PROGRAM)
        else:
            print("ERROR: Not an instruction: {}".format(instr))
            self._generate_trap(ILLEGAL_INSTRUCTION)
        

    # TODO: do error checking in all these.
    # Could check for illegal addresses, etc.
    def handle_jmp(self, dst):
        if self.isregister(dst):
            self._registers['pc'] = self._registers[dst]
        else:
            self._registers['pc'] = eval(dst)
        
    def handle_jez(self, src, dst):
        if not self.isregister(src):
            print("Illegal instruction")
            return
        if self._registers[src] == 0:
            if self.isregister(dst):
                self._registers['pc'] = self._registers[dst]
            else:
                self._registers['pc'] = eval(dst)
        else:
            self._registers['pc'] += 1
            
    def handle_jnz(self, src, dst):
        if not self.isregister(src):
            print("Illegal instruction")
            return
        if self._registers[src] != 0:
            if self.isregister(dst):
                self._registers['pc'] = self._registers[dst]
            else:
                self._registers['pc'] = eval(dst)
        else:
            self._registers['pc'] += 1
            
    def handle_jlz(self, src, dst):
        if not self.isregister(src):
            print("Illegal instruction")
            return
        if self._registers[src] < 0:
            if self.isregister(dst):
                self._registers['pc'] = self._registers[dst]
            else:
                self._registers['pc'] = eval(dst)
        else:
            self._registers['pc'] += 1

    def handle_jgz(self, src, dst):
        if not self.isregister(src):
            print("Illegal instruction")
            return
        if self._registers[src] > 0:
            if self.isregister(dst):
                self._registers['pc'] = self._registers[dst]
            else:
                self._registers['pc'] = eval(dst)
        else:
            self._registers['pc'] += 1

    def _get_value_at(self, addr):
        '''addr is "*<someval>".  return the value from
        RAM at the addr, which might be decimal
        or hex.'''
        addr = eval(addr[1:])
        return self._mmu._get_value_at(addr)

    def _get_srcval(self, src):
        if self.isregister(src):
            return self._registers[src]
        elif src[0] == '*':
            return self._get_value_at(src)
        else:   # assume src holds a literal value
            return eval(src)    # handles decimal and hex values.
            # TODO: does the above handle putting strings in memory too?  It should
            # allow single characters, perhaps.


    def handle_mov(self, src, dst):
        '''move value from a src to a dst.  src can be one of:
        literal value:          5
        value in memory:        *4
        value in register:      reg2
        dst can be one of:
        memory location:        4
        register name:          reg1
        memory location in reg: *reg1
        You cannot mov a value from RAM into RAM: you must use
        a register.
        '''
        srcval = self._get_srcval(src)

        if self.isregister(dst):
            self._registers[dst] = srcval
        elif dst[0] == '*':    # for *<register>
            if self.isregister(dst[1:]):
                self._mmu._set_value(self._registers[dst[1:]], srcval)
            else:
                print("Illegal instruction")
                return
        else:   # assume dst holds a literal value
            self._mmu._set_value(eval(dst), srcval)

    def handle_add(self, src, dst):
        srcval = self._get_srcval(src)

        if self.isregister(dst):
            self._registers[dst] += srcval
        elif dst[0] == '*':    # for *<register>
            if self.isregister(dst[1:]):
                self._mmu._increase_value(self._registers[dst[1:]], srcval)
            else:
                print("Illegal instruction")
                return
        else:   # assume dst holds a literal value
            self._mmu._increase_value(eval(dst), srcval)

                 
    def handle_sub(self, src, dst):
        srcval = self._get_srcval(src)

        if self.isregister(dst):
            self._registers[dst] -= srcval
        elif dst[0] == '*':    # for *<register>
            if self.isregister(dst[1:]):
                self._mmu._increase_value(self._registers[dst[1:]], -srcval)
            else:
                print("Illegal instruction")
                return
        else:   # assume dst holds a literal value
            self._mmu._increase_value(eval(dst), -srcval)

    def handle_call(self, fname):
        self._os.syscall(fname, self._reg0, self._reg1, self._reg2)

    def _generate_trap(self, reason):
        """Generate a software interrupt -- aka a trap.
        Store the reason for the trap in register 0."""
        
        self._registers['reg0'] = reason
        self.take_interrupt_mutex()
        self.add_interrupt_addr(SOFTWARE_TRAP_DEV_ID)
        self.set_interrupt(True)
        self.release_interrupt_mutex()

    def _timer_isr(self):
        '''Timer interrupt handler.  Pass control to the OS.'''
        self._os.timer_isr(self)

    def _trap_isr(self):
        '''Software interrupt handler.  Pass control to the OS.
        The reason for the software trap is found in register 0, so
        pass that also as a parameter to the OS handler.'''
        self._os.trap_isr(self, self._registers['reg0'])

    def set_stop_cpu(self, val):
        """Call this to stop the CPU because there are no more processes
        to execute."""
        self._stop = val

    def set_mmu_registers(self, low, high):
        #self._mmu._set_reloc_register(self._os.get_low_mem())
        #self._mmu._set_limit_register(self._os.get_high_mem() - self._os.get_low_mem())
        self._mmu._set_reloc_register(low)
        self._mmu._set_limit_register(high-low)