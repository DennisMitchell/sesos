from sys import exit

def append(instruction_index):
	global code_integer, code_shift
	code_shift += 3
	code_integer |= instruction_index << code_shift

code_integer = 0
code_shift = 0

def assemble(source):
	global code_integer
	flags = b'mask numin numout'.split()
	#                 0   1   2   3   4   5   6   7   8   9
	instructions = b'jmp jnz get put sub add rwd fwd nop jne'.split()
	invalid_pairs = ((0, 1), (1, 0), (4, 2), (4, 4), (4, 5), (5, 2), (5, 4), (5, 5), (6, 6), (6, 7), (7, 6), (7, 7))
	last_index = -1

	for linenumber, line in enumerate(source.splitlines(), 1):
		for command in line.split(b';')[0].split(b','):
			command = command.lstrip()
			tokens = command.split()
			if len(tokens) > 2:
				exit('Too many arguments in command %s on line %u.' % (command, linenumber))
			if tokens:
				if tokens[0] == b'set':
					try:
						code_integer |= 1 << flags.index(tokens[1])
					except:
						exit('Missing or invalid argument to set directive in command %s on line %u.' % (command, linenumber))
				else:
					try:
						instruction_index = instructions.index(tokens[0])
					except:
						exit('Unrecognized instruction %s on line %u.' % (command, linenumber))
					if (last_index, instruction_index) in invalid_pairs:
						exit('Invalid instruction sequence on line %u: %s may not follow %s.' % (linenumber, command, last_command))
					if instruction_index < 4:
						if len(tokens) > 1:
							exit('Too many arguments in command %s on line %u.' % (line, linenumber))
						append(instruction_index)
					elif instruction_index < 8:
						try:
							append(instruction_index)
							instruction_index &= -2
							repetitions = int(tokens[1])
							assert repetitions > 0
						except:
							exit('Missing or invalid argument to instruction in command %s on line %u.' % (command, linenumber))
						if instruction_index & 2:
							for bit in map(int, bin(repetitions)[3:]):
								append(instruction_index | bit)
						else:
							repetitions -= 1
							to_append = []
							while repetitions > 0:
								repetitions, digit = divmod(repetitions - 1, 3)
								to_append.append((2, 4, 5)[digit])
							for instruction in reversed(to_append):
								append(instruction)
					else:
						append((instruction_index - 7) & 1)
						append((instruction_index - 7) >> 1)
					last_index = instruction_index
					last_command = command
					last_linenumber = linenumber

	if last_index == 0:
		exit('Invalid instruction sequence on line %u: Command %s must be followed by another instruction.' % (last_linenumber, last_command))
	return code_integer.to_bytes(-(code_integer.bit_length() // -8), 'little')
