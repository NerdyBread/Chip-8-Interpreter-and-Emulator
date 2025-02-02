# Chip-8 Interpreter/System Emulator In Python

## Next Steps

- Debugger
- Disassembler
- Other screen modes and added support for SuperChip
- (In the very far future) A Nintendo Gameboy emulator


## Thoughts

This is my first real "resume worthy" project I would say. I'm actually proud of it and excited for what's next.
I tried to tackle this a number of years ago, but it didn't go well.
I didn't test well nor did I know how to, and I relied far too much on doing exactly what my resources did, even when I knew on a 
gut level that it may not have been the best way. I also jumped into coding too quickly/with not enough research beforehand; I didn't
even really grasp the difference between the interpreter for the chip8 language and the emulator for the machine running it.
I'm beyond happy with the way I did it this time, and the rush I got when the code that I truly wrote was running any ROM I threw at
it felt so good.
Definitely have some things to tinker with here before I do anything more advanced, namely the pygame rendering is very... blinky? I'm struggling to find the right way to describe it but the graphics just are drawn and then disappear and then are redrawn really fast, there's no fade or anything.

## Resources:

Thank you to all of these brilliant people who I would've struggled a lot more without
- [INCREDIBLE collection of Chip-8 testing ROMS created and maintained by Timendus](https://github.com/Timendus/chip8-test-suite)
- [Cowgod's Chip-8 Technical Reference (v1.0)](http://devernay.free.fr/hacks/chip8/C8TECH10.HTM#0.0)
- [trapexit's Github Repository of Chip-8 Reference Material](https://github.com/trapexit/chip-8_documentation/tree/master)
- [Interesting site detailing execution time of each opcode](https://jackson-s.me/2019/07/13/Chip-8-Instruction-Scheduling-and-Frequency.html)
