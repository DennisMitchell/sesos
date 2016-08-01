from collections import defaultdict
from locale import getlocale
from sys import exit, stderr, stdin, stdout

def add(argument):
	global code_head
	data[data_head] += argument
	data[data_head] &= mask
	code_head += 1

def fwd(argument):
	global code_head, data_head
	data_head += argument
	code_head += 1

def get(_):
	global code_head
	if numeric_input:
		try:
			data[data_head] = int(input())
		except:
			data[data_head] = 0
	else:
		try:
			char = stdin.buffer.read(1) if mask > 0 else stdin.read(1)
			data[data_head] = ord(char or '\0') & mask
		except:
			exit('Invalid input byte sequence for encoding %s.'	% getlocale()[1])
	code_head += 1

def jmp(_):
	global code_head
	code_head = markers[code_head]

def nop(_):
	global code_head
	code_head += 1

def jne(_):
	global code_head
	if numeric_input:
		try:
			data[data_head] = int(input()) & mask
			code_head = markers[code_head] + 1
		except:
			data[data_head] = 0
			code_head += 1
	else:
		try:
			char = stdin.buffer.read(1) if mask > 0 else stdin.read(1)
			if char:
				code_head = markers[code_head] + 1
			else:
				code_head += 1
			data[data_head] = ord(char or '\0')
		except:
			exit('Invalid input byte sequence for encoding %s.'	% getlocale()[1])

def jnz(_):
	global code_head
	if data[data_head]:
		code_head = markers[code_head] + 1
	else:
		code_head += 1

def rwd(argument):
	global code_head, data_head
	data_head -= argument
	code_head += 1

def put(do_not_debug):
	global code_head
	if numeric_output:
		print(data[data_head])
	else:
		if mask > 0:
			if do_not_debug:
				stdout.buffer.write(bytes([data[data_head]]))
			else:
				print(bytes([data[data_head]]))
		else:
			try:
				if do_not_debug:
					print(chr(data[data_head]), end = '')
				else:
					print(repr(chr(data[data_head])))
			except:
				exit('Invalid code point (%d) for encoding %s.'	% (data[data_head], getlocale()[1]))
	code_head += 1

def sub(argument):
	global code_head
	data[data_head] -= argument
	data[data_head] &= mask
	code_head += 1

def say_and_exit(exit_code):
	print('\nExecuted %u commands.' % commands)
	exit(exit_code)

def set_entry_marker(operator):
	global level
	level += 1
	markers_open.append(code_index)
	code.append([operator, 1])

def set_exit_marker(operator):
	global code_head, level
	level -= 1
	code_head = min(level, code_head)
	marker = level if level < 0 else markers_open.pop()
	markers[marker] = code_index
	markers[code_index] = marker
	code.append([operator, 1])

global mask, numeric_input, numeric_output
code = []
code_head = 0
code_index = -1
commands = 0
data = defaultdict(lambda: 0, {0: 0})
data_head = 0
level = 0
markers = {}
markers_open = []

def execute(source, count, debug):
	global code_head, code_index, commands, level, mask, numeric_input, numeric_output
	operators = (jmp, jnz, get, put, sub, add, rwd, fwd)
	operators_rle = ((sub, sub), (sub, add), (sub, get), (add, sub), (add, add), (add, get), (rwd, rwd), (rwd, fwd), (fwd, rwd), (fwd, fwd))
	operators_value = {rwd: 0, fwd: 1, get: -1, sub: 0, add: 1}
	base3_operators = (sub, add)

	code_integer = int.from_bytes(source, 'little')

	mask = 0xff if code_integer & 1 else -1
	code_integer >>= 1
	numeric_input = code_integer & 1 > 0
	code_integer >>= 1
	numeric_output = code_integer & 1 > 0
	code_integer >>= 1

	while code_integer:
		operator_last = code[-1][0] if code else nop
		operator = operators[code_integer & 7]
		code_integer >>= 3
		if (operator_last, operator) in operators_rle:
			code[-1][1] *= 2 + (operator_last in base3_operators)
			code[-1][1] += operators_value[operator]
			continue
		code_index +=1
		operator_next = operators[code_integer & 7]
		if operator == jmp:
			if operator_next != jnz:
				set_entry_marker(jmp)
			else:
				set_exit_marker(jne)
				code_integer >>= 3
		elif operator == jnz:
			if operator_next != jmp or code_integer == 0:
				set_exit_marker(jnz)
			else:
				set_entry_marker(nop)
				code_integer >>= 3
		else:
			code.append([operator, 1])

	level -= code_head
	code.extend([[jnz, 1]] * level)
	code.append([say_and_exit if count else exit, 0])
	code.extend([[jmp, 1]] * -code_head)

	while markers_open:
		code_index += 1
		marker = markers_open.pop()
		markers[marker] = code_index
		markers[code_index] = marker

	if code[code_head][0] == jmp:
		if code_head:
			code[markers[code_head]][0] = jne
		else:
			code[code_head][0] = nop

	while True:
		operator, argument = code[code_head]
		if debug:
			print('    %s %s' % (operator.__name__, argument))
			if operator == put:
				put(do_not_debug = False)
			else:
				operator(argument)
			data[data_head]
			tape = data.keys()
			min_tape, max_tape = min(tape), max(tape)
			len_tape = max(len(str(min_tape)), len(str(max_tape)))
			for key in range(min_tape, max_tape + 1):
				print('    %*d%s %d' % (len_tape, key, ':>'[key == data_head], data[key]))
			print()
		else:
			operator(argument)
		commands += 1