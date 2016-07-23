# Sesos

Sesos &ndash; meaning *brains* (culinary) in Spanish &dash;  is a recreational programming language based on [brainfuck].

Unlike the latter, it is concise, can be typed easily, has somewhat flexible I/O, and is safe for work. However, programming in Sesos is not substantially easier than programming in its parent language.

## Sesos assembly

The typable way of writing Sesos programs is SASM (**s**esos **as**se**m**bly). Each non-empty line of SASM must contain an assembler directive or an instruction. Every line can contain multiple commands, which must be separated by `,`. Additionally, inline comments can be used by prefixing them with a `;`.

The tokens of each command &ndash; and the commands themselves &ndash; may be indented, followed and separated by any combination of tabulators and spaces. The lines themselves may be separated by any combination of linefeeds, carriage returns, vertical tabs and formfeeds.

### Assembler directives

There are three different assembler directives. All directives apply globally and may appear anywhere in the SASM file. Multiple occurrences of the same directive have the same effect as a single occurrence.

    set mask

By default, the cells of Sesos' data tape can hold arbitrary precision integers. This directive applies the bit mask `0xff` after cell-altering operations, thus replacing arbitrary precision arithmetic with unsigned 8-bit arithmetic.

    set numin

By default, Sesos reads characters (or bytes, for unsigned 8-bit arithmetic) from STDIN. This directive changes that behavior; Sesos will read one signed [integer literal] per line instead.

    set numout

By default, Sesos writes characters (or bytes, for unsigned 8-bit arithmetic) to STDOUT. This directive changes that behavior; Sesos will write one decimal integer per line instead.

### Instructions

Each Sesos program consist of a finite (but arbitrarily large) code tape representing the instructions and a doubly-infinite data tape of cells containing either arbitrary precision integers or unsigned 8-bit integers. All cells of the data tape initially contain zeros. Additionally, there are a *code head* that marks the current position on the code tape, and a *data head* that marks the current position on the data tape.

Sesos can interpret ten different instructions that modify the contents of the data tape's cells, move the code or data head, read input from STDIN, or write output to STDOUT. Four of the instructions require a single positive integer argument, in form of a signed [integer literal]. The remaining instructions do not take arguments.

Unless specified otherwise, all instructions move the code head to the next instruction after completing their task.

    fwd <n>

This instruction moves the data head **n** cells to the right. **n** must be a positive integer.

    rwd <n>

This instruction moves the data head **n** cells to the left. **n** must be a positive integer.

    add <n>

This instruction adds **n** to the cell under the data head. The exact behavior depends on the assembler directives. **n** must be a positive integer.

    sub <n>

This instruction subtracts **n** from the cell under the data head. The exact behavior depends on the assembler directives. **n** must be a positive integer.

    get

This instruction reads a single cell value from STDIN and writes it to the cell under the data head. The exact behavior depends on the assembler directives.

When EOF is reached, the cell under the data head is zeroed. For numeric input, an invalid signed [integer literal] will also zero the cell. For character input, a byte sequence that cannot be decoded in the default locale is a runtime error.

    put

This instruction write the value of the cell under the data to STDOUT. The exact behavior depends on the assembler directives.

    jmp

This instruction sets an entry marker at the current position of the code head, then unconditionally jumps to the corresponding exit marker set by either `jnz` or `jne`.

    nop

This instruction sets an entry marker at the current position of the code head. Unlike `jmp`, it does not jump to the corresponding exit marker.

    jnz

This instruction sets an exit marker at the current position of the code head. If the cell under the data head is non-zero, it jumps to the right of the corresponding entry marker.

    jne

This instruction executes `get`. If `get` did not hit EOF, it jumps to the right of the corresponding entry marker.

### Restrictions

Because of how the instructions are encoded in Sesos' binary files, certain instructions cannot be used under certain circumstances.

* `fwd` may not immediately follow `fwd` or `rwd`.
* `rwd` may not immediately follow `fwd` or `rwd`.
* `add` may not immediately follow `add` or `sub`.
* `sub` may not immediately follow `add` or `sub`.
* `jnz` may not immediately follow `jmp`.
* `jmp` may not immediately follow `jnz`.
* `jmp` must be followed by another instruction.
* `nop` must be followed by another instruction.

### Special cases

Leading `jmp` instructions may be omitted if the corresponding exit marker (`jnz` or `jne`) is present. Doing so will omit them from the generated binary file as well; the interpreter will add them as needed.

Likewise, trailing `jnz` instructions may be omitted if the corresponding entry marker (`jmp` or `nop`) is present.

Finally, if the entry marker corresponding to a `jnz` instruction is the first (possibly implicit) instruction of the program, it will be promoted to a `jne` instruction. Specifying `jnz` or `jne` in SASM will generate a different &ndash; but functionally equivalent &ndash; binary file.

## Sesos binary

SBIN (**s**esos **bin**ary) files can be created either by hand or by assembling the corresponding SASM.

A binary Sesos file consist of an arbitrary number of triads (consisting of three bits each) that encode directives, instructions, or instructions arguments. These triads are padded by adding or removing trailing **0** bits to reach an entire number of bytes.

Alternatively, an SBIN file can be viewed as a single non-negative integer **n**, expressed in base 256 in little-endian byte order.

![integer source code][integer source code]

Here, each **t<sub>k</sub>** represents a triad.

### Directives

The first triad is a bit field. If `mask` is set, so is the least significant bit **t<sub>0</sub>**; if `numin` is set, so is the middle bit **t<sub>0</sub>**; if `numout` is set, so is the most significant bit of **t<sub>0</sub>**.

### Instructions

The eight instructions that have a counterpart in Sesos' parent language are encoded as a single triad each. The remaining instructions (`nop` and `jne`) are encoded as a pair of triads.

Instruction | Triad sequence
:----------:|:---------------:
`jmp`       | **0**
`jnz`       | **1**
`get`       | **2**
`put`       | **3**
`sub`       | **4**
`add`       | **5**
`rwd`       | **6**
`fwd`       | **7**
`nop`       | **1 0**
`jne`       | **0 1**

### Instruction arguments

Arguments to `add`, `sub`, `fwd`, and `rwd` are encoded as zero or more triads, immediately after the corresponding instructions.

For `add` and `sub`, **4** (`sub`) represents an even digit, while **5** (`add`) represents an odd digit. Likewise, for `fwd` and `rwd`, **6** (`rwd`) represents an even digit, while **7** (`fwd`) represents an odd digit.

The argument of each of these four instructions starts out as **1**. If followed by zero triads encoding their arguments, **1** is the final value.

Each digit triad that follows the instruction doubles the value of the argument. Additionally, if the digit is odd, it increments the argument once after doubling it.

Essentially, the argument is represented as a big-endian base 2 literal, where the instruction itself serves as the most-significant digit.

### Generating SBIN files

To generate an SBIN file with the interpreter, save the corresponding SASM in a file with extension `sasm`, and run the interpreter with the `-a` option and that file's basename as command-line arguments.

This will create a binary file with the same basename and extension `sbin`.

### Executing SBIN files

To execute an SBIN file &ndash; which must have the extension `sbin` &ndash; run the interpreter with the file's basename as command-line argument.

You can optionally set any combination of the following options.

Option | Description
:-----:|------------
`-c`   | Count how many commands are executed.
`-d`   | Print debugging information for each executed command.

## Online interpreters

The official [Sesos online interpreter] can be found on [Try it online!] To use it, simply write the desired SASM in the *Code* field, and the interpreter will generate and execute the corresponding SBIN file.

If the *Debug* option is set, the interpreter will print the generated binary code in form of a reversible hexdump.

[brainfuck]: https://en.wikipedia.org/wiki/Brainfuck
[integer literal]: https://docs.python.org/3/reference/lexical_analysis.html#integer-literals
[integer source code]: http://i.stack.imgur.com/MRJhl.png
[Sesos online interpreter]: http://sesos.tryitonline.net
[Try it online!]: http://tryitonline.net