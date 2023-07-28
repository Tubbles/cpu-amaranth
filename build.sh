#!/bin/bash

venvpy="/var/venv/bin/python"

"${venvpy}" ./assemble_rom.py -i rom.s -o rom_file && hexdump -C rom_file && "${venvpy}" ./cpu.py
