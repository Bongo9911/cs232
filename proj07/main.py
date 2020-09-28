import calos
from cpu import CPU, MAX_CHARS_PER_ADDR
from ram import RAM, MMU


'''
Architecture Description:
There are 3 registers, reg0, reg1, reg2, and a program counter
register, pc.

There are 1024 words of RAM, from addresses 0 to 1023.  The number
of bits/bytes in a word is not defined:
o Any positive or negative number fits in a word.
o Every instruction, including arguments, fits in a word.
o A string of up to 4 characters fits in a word: this is
  indicated by surrounding the string with single quotes.


Assembly Language Instructions:
mov <src> <dst>   move value from <src> to <dst>
add <val> <dst>   add value to <dst>
sub <val> <dst>   sub value from <dst>

<src> and <dst> can be a register name, a <value>, or *<value>.
*<src> means the contents of RAM at the address <src>.
*<reg> means the contents of RAM at the location referenced by reg.
You cannot move values from one RAM location to another.
<value> can be given in decimal or hexidecimal.
<val> can be a literal value or a register name.

jmp <dst> means change pc to <dst>.
jez <reg> <dst> means change pc to <dst> if register <reg> is 0.
jnz <reg> <dst> means change pc to <dst> if register <reg> is not 0.
jgz <reg> : > 0
jlz <reg> : < 0

end  means end the program

Sample program: multiply values in addresses 0 and 1, leaving
result in location 2.

20: mov 0 4	     # put 0 into the destination in case val1 or val2 are 0.
21: mov *0 reg2      # move 1st value to reg2
22: jez reg2 31      # we are done if val1 is 0
23: mov *1 reg1      # move 2nd value to reg1
24: jez reg1 31      # we are done if val2 is 0
25: mov reg2 reg0    # copy reg2 to reg0
26: sub 1 reg1       # loop: subtract 1 from val2
27: jez reg1 30      # if == 0, we are done looping
28: add reg0 reg2    # add reg0 to reg2  where we accumulate result
29: jmp 26           # repeat the loop
30: mov reg2 2       # store result in location 2
31: end

'''


class Monitor:
    def __init__(self, ram):
        self._debug = False
        self._ram = ram
        
        self._os = calos.CalOS()
        self._cpus = [ CPU(self._ram, self._os, 0) ] # , CPU(self._ram, self._os, 1) ]
        # self._cpus = [ CPU(self._ram, self._os, 0) ]
        self._os.set_cpus(self._cpus)
        self.set_debug(False)

    def run(self):
        print("Monitor: enter ? to see options.")
        while True:
            if self._debug:
                for cpu in self._cpus:
                    print(cpu)
                print("-" * 75)

            instr = input("MON> ").strip()
            if instr == '':
                # blank line
                continue
            if instr == '?':
                print("C <addr>: put code into RAM starting at addr")
                print("D <addr>: put data values into RAM starting at addr")
                print("S <start> <end>: show memory from start to end")
                print("X <addr>: execute program starting at addr")
                print("L <addr> <tapename>: load a program from tape to bytes starting at addr")
                print("W <start> <end> <tapename>: write bytes from start to end to tape")
                print("R : Start up OS and execute ready queue")
                print("! : Toggle debugging on or off -- off at startup.")
                continue

            # Remove all commas, just in case.
            instr = instr.replace(",", "")
            
            # 0 argument cases
            numargs = len(instr.split())
            if numargs == 1:
                self._zero_arg_instr(instr)
            elif numargs == 2:
                self._one_arg_instr(instr)
            elif numargs == 3:
                self._two_arg_instr(instr)
            elif numargs == 4:
                self._three_arg_instr(instr)
            else:
                print("Unknown or badly formatted instruction: too many arguments")
                    
    def _zero_arg_instr(self, instr):
        if instr.startswith("!"):
            self.set_debug(not self._debug)
        elif instr.upper().startswith("R"):
            self._os.run()
        else:
            print("Unknown command")

    def _one_arg_instr(self, instr):
        try:
            arg1 = eval(instr.split()[1])
        except:
            print("Illegal format: ", instr.split()[1])
            return
        if instr.upper().startswith('C '):
            self._enter_program(arg1)
        elif instr.upper().startswith('D '):
            self._poke_ram(arg1)
        elif instr.upper().startswith('X '):
            self._run_program(arg1)
        else:
            print("Unknown command")

    def _two_arg_instr(self, instr):
        if instr.upper().startswith('S '):
            try:
                startaddr = eval(instr.split()[1])
                endaddr = eval(instr.split()[2])
                self._dump_ram(startaddr, endaddr)
            except:
                print("Illegal format")

        elif instr.upper().startswith('L '):
            try:
                startaddr = eval(instr.split()[1])
                tapename = instr.split()[2]
                self._load_program(startaddr, tapename)
            except:
                print("Illegal format")
        else:
            print("Unknown command")


    def _three_arg_instr(self, instr):
        if instr.upper().startswith('W '):
            try:
                startaddr = eval(instr.split()[1])
                endaddr = eval(instr.split()[2])
                tapename = instr.split()[3]
                self._write_program(startaddr, endaddr, tapename)
            except:
                print("Illegal format")
        else:
            print("Unknown command")

    def set_debug(self, debug):
        self._debug = debug
        for cpu in self._cpus:
            cpu.set_debug(self._debug)
        self._os.set_debug(self._debug)

    def _load_program(self, startaddr, tapename, procname=None):
        '''Load a program into memory from a stored tape (a file) starting
        at address startaddr.  Create a PCB for the program and add to
        the ready q.  Use the first part of the tapename as the procname,
        if not provided. 
        '''
        
        if procname is None:
            # Lop off .* from the end.
            procname = tapename[: tapename.find(".")]
        pcb = None
        try:
            with open(tapename, "r") as f:
                pcb = calos.PCB(procname)
                if self._debug:
                    print("Created PCB for process {}".format(procname))
                addr = startaddr
                pcb.set_low_mem(addr)
                for line in f:
                    line = line.strip()
                    if line == '':
                        continue            # skip empty lines
                    if line.startswith('#'):    
                        continue	    # skip comment lines
                    if line.isdigit():
                        # data
                        self._ram[addr] = int(line)
                        addr += 1
                    elif line.startswith("__main:"):
                        self._handle_main_label(addr, line, pcb)
                    elif line.startswith("__data:"):
                        self._handle_data_label(addr, line, pcb)
                    else:   # the line is regular code: store it in ram
                        self._ram[addr] = line
                        addr += 1
            print("Tape loaded from {} to {}".format(startaddr, addr))
            if self._debug:
                print(pcb)
        except FileNotFoundError:
            print("File not found")
        if pcb is not None:
            self._os.add_to_ready_q(pcb)

    def _handle_main_label(self, addr, line, pcb):
        """line from the file has format __main: <addr>,
        which indicates where the entry point is.  Note: all
        addresses in the code are logical.
        e.g., __main: 0 means the code assumes
        the executable lives at 0.  It might be loaded
        into some other location, which is the value in addr.
        """
        if len(line.split()) != 2:
            raise ValueError("Illegal format: __main: must be followed by entrypoint address.")
        logical_addr = int(line.split()[1])
        pcb.set_entry_point(logical_addr)
        if self._debug:
            print("__main found at physical location", addr, "but logical addr", logical_addr)

    def _handle_data_label(self, addr, line, pcb):
        if len(line.split()) != 2:
            raise ValueError("Illegal format: __data: must be followed by high memory address.")
        num_bytes = int(line.split()[1])
        high_addr = addr + num_bytes
        pcb.set_high_mem(high_addr)
        if self._debug:
            print("__data begins at addr", addr, "and ends at the addr", high_addr)

    def _write_program(self, startaddr, endaddr, tapename):
        '''Write memory from startaddr to endaddr to tape (a file).'''
        with open(tapename, "w") as f:
            addr = startaddr
            while addr <= endaddr:
                f.write(str(self._ram[addr]) + "\n")
                addr += 1
        print("Tape written from {} to {}".format(startaddr, addr - 1))

    def _run_program(self, addr):
        # Set the program counter and start the CPU running.
        self._cpus[0].set_pc(addr)
        self._cpus[0].start()		# call run()
        self._cpus[0].join()		# wait for it to end

    def _enter_program(self, starting_addr):
        # TODO: must make sure we enter program starting on even boundary.
        curr_addr = int(starting_addr)
        if not self._ram.is_legal_addr(curr_addr):
            print("Illegal address")
            return
        while True:
            code = input("Enter code ('.' to end) [{}]> ".format(curr_addr))
            if code == '.':
                return
            self._ram[curr_addr] = code
            curr_addr += 1
            if not self._ram.is_legal_addr(curr_addr):
                print("End of RAM")
                return
        
    def _poke_ram(self, starting_addr):
        curr_addr = int(starting_addr)
        if not self._ram.is_legal_addr(curr_addr):
            print("Illegal address")
            return
        while True:
            data = input("Enter value (. to end) [{}]> ".format(curr_addr))
            if data == '.':
                return
            if data[0] == "'":    # user entering string, max 4 characters.
                end = data.find("'", 1)
                if end == -1:
                    print("Bad string: no ending quote")
                    return
                if end > MAX_CHARS_PER_ADDR:
                    end = MAX_CHARS_PER_ADDR
                data = data[0:end] + "'"
                self._ram[curr_addr] = data
            else:
                try:
                    data = int(data)
                except:
                    print("Bad value")
                    return
                self._ram[curr_addr] = data
            curr_addr += 1
            if not self._ram.is_legal_addr(curr_addr):
                print("End of RAM")
                return

    def _dump_ram(self, starting_addr, ending_addr):
        curr_addr = int(starting_addr)
        if not self._ram.is_legal_addr(curr_addr):
            print("Illegal start address")
            return
        end_addr = int(ending_addr)
        if not self._ram.is_legal_addr(end_addr):
            print("Illegal end address")
            return
        if end_addr < curr_addr:
            print("Nothing to display")
            return
        while curr_addr <= end_addr:
            val = self._ram[curr_addr]
            if isinstance(val, int):
                print("[%04d] %d" % (curr_addr, val))
            else:
                print("[%04d] %s" % (curr_addr, val))
            curr_addr += 1
        
# Main
ram = RAM()

# Like BIOS
monitor = Monitor(ram) 
monitor.run()
