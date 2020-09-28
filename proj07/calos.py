import threading

DEFAULT_QUANTUM = 3   # very short -- for pedagogical reasons.

class CalOS:

    def __init__(self, debug=False):
        self.syscalls = { "test_syscall": self.test_syscall }
        self._ready_q = []
        self._timer_controller = None
        self._cpus = None
        self._debug = debug
        self._threads = []

        # Refers to the current process's PCB, per CPU
        self._current_proc = []

    def set_cpus(self, cpus):
        '''store a reference to the list of cpus'''
        self._cpus = cpus
        # Initialize the list of current_procs and threads
        self._current_proc = [None] * len(self._cpus)
        self._threads = [None] * len(self._cpus)

    def set_debug(self, debug):
        self._debug = debug

    def syscall(self, fname, val0, val1, val2):
        if not fname in self.syscalls:
            print("ERROR: unknown system call", fname)
            return
        self.syscalls[fname](val0, val1, val2)

    def test_syscall(self, val0, val1, val2):
        print("Test system call called!")

    def set_timer_controller(self, t):
        self._timer_controller = t

    def add_to_ready_q(self, pcb):
        '''Add pcb to the ready queue, and set the state of the process to READY.'''
        pcb.set_state(PCB.READY)
        self._ready_q.append(pcb)

        if self._debug:
            print("add_to_ready_q: queue is now:")
            for p in self._ready_q:
                print("\t" + str(p))
            print("Num ready processes = {}".format(len(self._ready_q)))

    def timer_isr(self, cpu):
        '''Called when the timer expires. If there is no process in the
        ready queue, reset the timer and continue.  Else, context_switch.
        '''

        # All ISRs do this: save registers of current process.
        self._current_proc[cpu.get_num()].set_registers(cpu.get_registers())


        if len(self._ready_q) == 0:
            # Leave current proc in place, as running: just reset the timer.

            self.reset_timer(cpu)
            # Required of all ISRs: restore the registers before returning
            # (if no context switch)
            cpu.set_registers(self._current_proc[cpu.get_num()].get_registers())
            cpu.set_mmu_registers(self._current_proc[cpu.get_num()].get_low_mem(), self._current_proc[cpu.get_num()].get_high_mem())
            return

        self.context_switch(cpu)

        # reset the timer (to the quantum of the (new) current_proc).
        self.reset_timer(cpu)

    def trap_isr(self, cpu, reason):
        '''Called when a software trap has been generated. The reason is
        passed in.'''

        # NOTE: no need to save registers to current_proc because
        # at this point, if we get a trap, we won't be starting that
        # process again -- it is done, normally or due to error.

        import cpu as cpumodule
        if reason == cpumodule.END_OF_PROGRAM:
            print("PROGRAM ENDED NORMALLY")
        elif reason == cpumodule.ILLEGAL_INSTRUCTION:
            print("BAD INSTRUCTION: ENDING PROGRAM")

        # Program ended.  Context switch to first process
        # in the ready queue, if available.
        if len(self._ready_q) > 0:
            self._assign_proc_to_cpu(cpu)
            #print("Low is now", self._current_proc[cpu.get_num()].get_low_mem(), "High is now", self._current_proc[cpu.get_num()].get_high_mem())
        else:
            # No more processes to run, so stop the CPU.
            cpu.set_stop_cpu(True)

    def context_switch(self, cpu):
        '''Do a context switch between the current_proc and the process
        on the front of the ready_q.
        '''
        old_proc = self._current_proc[cpu.get_num()]
        new_proc = self._ready_q.pop(0)
        if self._debug:
            print("Switching procs from {} to {}".format(old_proc.get_name(), new_proc.get_name()))

        old_proc.set_registers(cpu.get_registers())
        cpu.set_registers(new_proc.get_registers())

        self.add_to_ready_q(old_proc)
        new_proc.set_state(PCB.RUNNING)
        self._current_proc[cpu.get_num()] = new_proc
        cpu.set_mmu_registers(self._current_proc[cpu.get_num()].get_low_mem(), self._current_proc[cpu.get_num()].get_high_mem())


    def reset_timer(self, cpu):
        '''Reset the timer's countdown to the value in the current_proc's
        PCB.'''
        cpu.reset_timer(self._current_proc[cpu.get_num()].get_quantum())

    def run(self):
        '''Execute processes in the ready queue on all cpus --
        i.e., run the operating system!'''

        if self._debug:
            print("Calos.run() ready processes = {}".format(len(self._ready_q)))

        # Create a thread for each CPU.
        # For each cpu:
        #    dequeue the first process from the ready queue, and set up the CPU
        #    to run it.
        # Start each thread.
        # Join all threads.

        for idx in range(len(self._cpus)):
            if len(self._ready_q) == 0:
                break
            cpu = self._cpus[idx]
            self._threads[idx] = threading.Thread(target=cpu.run_cpu)

            self._assign_proc_to_cpu(cpu)
            cpu.set_stop_cpu(False)   # power up the CPU.

            if self._debug:
                print("Running", self._current_proc[cpu.get_num()])

        # Start all the CPUs
        for t in self._threads:
            if t is not None:
                t.start()

        # Wait for all CPUs to be done, which is when *all* processes are done.
        for idx in range(len(self._cpus)):
            cpu = self._cpus[idx]
            if self._threads[idx] is None:
                continue
            self._threads[idx].join()
            if self._debug:
                print("CalOS.run(): done with", cpu)

            # TODO: move this to an ISR where end is handled as a
            # software interrupt.  Maybe.
            self._current_proc[cpu.get_num()].set_state(PCB.DONE)

            if self._debug:
                print("Done running {}, num ready_processes now {}".
                      format(self._current_proc[cpu.get_num()], len(self._ready_q)))

    def _assign_proc_to_cpu(self, cpu):
        new_proc = self._ready_q.pop(0)
        self._current_proc[cpu.get_num()] = new_proc
        self.reset_timer(cpu)
        cpu.set_registers(new_proc.get_registers())
        cpu.set_mmu_registers(self._current_proc[cpu.get_num()].get_low_mem(), self._current_proc[cpu.get_num()].get_high_mem())
        new_proc.set_state(PCB.RUNNING)

class PCB:
    '''Process control block'''

    NEW, READY, RUNNING, WAITING, DONE = "NEW", "READY", "RUNNING", "WAITING", "DONE"
    LEGAL_STATES = NEW, READY, RUNNING, WAITING, DONE

    # PID 0 is reserved for the IDLE process, which runs when there are no other
    # ready processes.
    next_pid = 1
    
    def __init__(self, name, pid=None):

        self._name = name
        if pid is None:
            self._pid = PCB.next_pid
            PCB.next_pid += 1
        else:
            self._pid = pid

        self._entry_point = None

        # These addresses define the limits of the memory assigned for this process.
        # The mem_low also represents the offset used for translation of logical
        # addresses in code to physical addresses in RAM.
        self._mem_low = None
        self._mem_high = None
        self._state = PCB.NEW

        # Used for storing state of the process's registers when it is not running.
        self._registers = {
            'reg0' : 0,
            'reg1' : 0,
            'reg2' : 0,
            'pc': 0
            }

        # Quantum: how long this process runs before being interrupted.
        self._quantum = DEFAULT_QUANTUM

    def set_entry_point(self, addr):
        self._entry_point = addr
        self._registers['pc'] = addr

    def get_entry_point(self):
        return self._entry_point

    def set_low_mem(self, low):
        self._mem_low = low

    def set_high_mem(self, high):
        self._mem_high = high

    def get_low_mem(self):
        return self._mem_low

    def get_high_mem(self):
        return self._mem_high

    def set_state(self, st):
        assert st in self.LEGAL_STATES
        self._state = st

    def get_state(self):
        return self._state

    def set_registers(self, registers):
        self._registers = registers
        
    def get_registers(self):
        return self._registers

    def get_quantum(self):
        return self._quantum

    def set_quantum(self, q):
        self._quantum = q

    def get_pid(self):
        return self._pid

    def get_name(self):
        return self._name

    def __str__(self):
        return "PCB({}): {}, state {}, entrypoint {}, low mem {}, high mem {}".\
               format(self._pid, self._name, self._state,
                      self._entry_point, self._mem_low, self._mem_high)
    
