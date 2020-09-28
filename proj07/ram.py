RAM_SIZE = 1024


class RAM:
	def __init__(self, size=RAM_SIZE):
		self._minAddr = 0
		self._maxAddr = RAM_SIZE - 1
		self._memory = []   # a list of values.  Could be #s or instructions.
		for i in range(size):
			self._memory.append(0)

	def __getitem__(self, addr):
		return self._memory[addr]

	def __setitem__(self, addr, val):
		self._memory[addr] = val

	def is_legal_addr(self, addr):
		return self._minAddr <= addr <= self._maxAddr

class MMU:
	def __init__(self, ram):
		self._ram = ram
		self._reloc = 0
		self._limit = 0

	def _get_value_at(self, addr):
		'''addr is "*<someval>". return the value from
		RAM at the addr, which might be decimal
		or hex.'''
		if(addr < self._limit):
			return self._ram[addr + self._reloc]
		else:
			raise ValueError("BAD ADDRESS %d: too high", addr)

	def _set_value(self, addr, value):
		'''addr is "*<someval>". change the value in
		RAM at the addr to the passed value'''
		if(addr < self._limit):
			self._ram[addr + self._reloc] = value
		else:
			raise ValueError("BAD ADDRESS %d: too high", addr)

	def _increase_value(self, addr, value):
		'''addr is "*<someval>".  increase the value in
		RAM at the addr by the passed value'''
		if(addr < self._limit):
			self._ram[addr + self._reloc] += value
		else:
			raise ValueError("BAD ADDRESS %d: too high", addr)

	def _set_reloc_register(self, value):
		self._reloc = value

	def _set_limit_register(self, value):
		self._limit = value