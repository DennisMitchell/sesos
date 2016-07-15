from sys import exit

def append(*instruction_indices):
	global code_integer, code_shift
	for index in instruction_indices:
		code_shift += 3
		code_integer |= index << code_shift

code_integer = 0
code_shift = 0

def assemble(source):
	global code_integer
	flags = b'mask numin numout'.split()
	instructions = b'jmp jnz get put sub add rwd fwd nop jne'.split()
	invalid_pairs = ({0, 1}, {4, 4}, {4, 5}, {5, 5}, {6, 6}, {6, 7}, {7, 7})
	last_index = -1

	for linenumber, line in enumerate(source.splitlines(), 1):
		tokens = line.split(b';')[0].split()
		if len(tokens) > 2:
			exit('Too many arguments on line %u: %s' % (linenumber, line))
		if tokens:
			if tokens[0] == b'set':
				try:
					code_integer |= 1 << flags.index(tokens[1])
				except:
					exit('Missing or invalid argument to set directive on line %u: %s' % (linenumber, line))
			else:
				try:
					instruction_index = instructions.index(tokens[0])
				except:
					exit('Unrecognized instruction on line %u: %s' % (linenumber, line))
				if {last_index, instruction_index} in invalid_pairs:
					exit('Invalid instruction sequence on line %u: %s may not follow %s' % (linenumber, line, last_line))
				if instruction_index < 4:
					if len(tokens) > 1:
						exit('Too many arguments on line %u: %s' % (linenumber, line))
					append(instruction_index)
				elif instruction_index < 8:
					try:
						append(instruction_index)
						instruction_index &= -2
						repetitions = int(tokens[1])
						assert repetitions > 0
					except:
						exit('Missing or invalid instruction argument on line %u: %s' % (linenumber, line))
					for bit in map(int, bin(repetitions)[3:]):
						append(instruction_index | bit)
				else:
					instruction_index -= 7
					append(instruction_index >> 1, instruction_index & 1)
				last_index = instruction_index
				last_line = line

	return code_integer.to_bytes(-(code_integer.bit_length() // -8), 'little')