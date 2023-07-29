.DEFAULT: all
.PHONY: all
all: test

build/rom_file: source/rom.s source/assemble_rom.py source/codes.py
	mkdir -p build
	source/assemble_rom.py -i source/rom.s -o build/rom_file

.PHONY: test
test: source/cpu.py source/codes.py build/rom_file
	source/cpu.py
