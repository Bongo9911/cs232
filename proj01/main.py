'''Main program for CalOS.  Starts up a Monitor from which you can
alter RAM, start the CPU, etc.

@author Victor Norman
@date 12/26/17

modified by: Dawson Buist
date: 02/08/20
'''


import time
import threading
import calos
from cpu import CPU
from ram import RAM


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
        self._cpu = None		# may have to become a list of cores
        self._debug = False
        self._ram = ram

    def run(self):   # called from monitor._cpu.start()
        print("Monitor: enter ? to see options.")
        while True:
            try:
                if self._debug:
                    print("State of the CPU is:")
                    print(str(self._cpu) + "\n" + ("-" * 75))

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
                    print("! : Toggle debugging on or off -- off at startup.")
                    print("R <addr>: Run the programs whose starting locations are in memory starting at addr")
                    continue

                # Remove all commas, just in case.
                instr = instr.replace(",", "")

                if instr.startswith("!"):
                    self._debug = not self._debug
                    continue

                try:
                    arg1 = eval(instr.split()[1])
                except:
                    print("Illegal format: ", instr.split()[1])
                    continue
                if instr.upper().startswith('C '):
                    self._enter_program(arg1)
                elif instr.upper().startswith('S '):
                    try:
                        endaddr = eval(instr.split()[2])
                    except:
                        print("Illegal format: ", instr.split()[2])
                        continue
                    self._dump_ram(arg1, endaddr)
                elif instr.upper().startswith('D '):
                    self._poke_ram(arg1)
                elif instr.upper().startswith('X '):
                    self._run_program(arg1)
                elif instr.upper().startswith('R '):
                    self._run_batch(arg1)
                elif instr.upper().startswith('L '):
                    try:
                        tapename = instr.split()[2]
                    except:
                        print("Illegal format: ", instr.split()[2])
                        continue
                    self._load_program(arg1, tapename)  # arg1 is startaddr
                elif instr.upper().startswith('W '):
                    try:
                        endaddr = eval(instr.split()[2])
                        tapename = instr.split()[3]
                    except:
                        print("Illegal format: ", instr.split()[2], instr.split()[3])
                        continue
                    self._write_program(arg1, endaddr, tapename)
                else:
                    print("Unknown command")
            except Exception as e:
                # TODO
                raise e

    def _load_program(self, startaddr, tapename):
        '''Load a program into memory from a stored tape (a file) starting
        at address startaddr.'''
        try:
            with open(tapename, "r") as f:
                addr = startaddr
                for line in f:
                    line = line.strip()
                    if line == '':
                        continue            # skip empty lines
                    if line.startswith('#'):    # skip comment lines
                        continue
                    if line.isdigit():
                        # data
                        self._ram[addr] = int(line)
                    else:                        # instructions or label
                        # Detect entry point label
                        if line == "__main:":
                            print("Main found at", addr)
                            # TODO: store entry point address.
                            continue
                        self._ram[addr] = line
                    addr += 1
            print("Tape loaded from %d to %d" % (startaddr, addr))
        except FileNotFoundError:
            print("File not found")

    def _write_program(self, startaddr, endaddr, tapename):
        '''Write memory from startaddr to endaddr to tape (a file).'''
        with open(tapename, "w") as f:
            addr = startaddr
            while addr <= endaddr:
                f.write(str(self._ram[addr]) + "\n")
                addr += 1
        print("Tape written from %d to %d" % (startaddr, addr - 1))

    def _run_program(self, addr):
        # creates a new thread, passing in ram, the os, and the
        # starting address
        self._cpu = CPU(self._ram, calos.CalOS(), addr, self._debug)
        self._cpu.start()		# call run()
        self._cpu.join()		# wait for it to end

    def _run_batch(self, addr):
        '''Creates a new CPU in batch mode so it can run multiple programs'''
        self._cpu = CPU(self._ram, calos.CalOS(), addr, self._debug, True)
        self._cpu.start()       # call run()
        self._cpu.join()        # wait for it to end


    def _enter_program(self, starting_addr):
        # TODO: must make sure we enter program starting on even boundary.
        curr_addr = int(starting_addr)
        if not self._ram.is_legal_addr(curr_addr):
            print("Illegal address")
            return
        while True:
            code = input("Enter code ('.' to end) [%d]> " % (curr_addr))
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
            data = input("Enter value (. to end) [%d]> " % (curr_addr))
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
