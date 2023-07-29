#!/usr/bin/env python3

import amaranth as am
from amaranth.build import Platform
from amaranth.lib import data
from amaranth.sim import Simulator
import os
import struct

from codes import Operation


class Cpu(am.Elaboratable):
    def __init__(self, rom_file="rom_file", word_size=8, addr_bus_width=8, num_aux_regs=8):
        bytes_in_word = int(word_size/8)

        # Params
        self.plain_rom = []
        with open(rom_file, "rb") as ifs:
            ifs.seek(0, os.SEEK_END)
            size = ifs.tell()
            self.rom = data.ArrayLayout(am.unsigned(word_size), size)
            self.rom_view = data.View(self.rom, am.Signal(word_size * size))
            ifs.seek(0)
            index = 0
            while ifs.tell() != size:
                self.plain_rom.append(struct.unpack(f"{bytes_in_word}B", ifs.read(bytes_in_word))[0])
                index += 1

        self.program_counter = am.Signal(addr_bus_width)
        self.operation = am.Signal(word_size, reset=Operation.NOP)
        self.input = am.Signal(word_size)
        self.output = am.Signal(word_size)
        self.registers = [am.Signal(word_size)] * num_aux_regs
        self.is_halted = am.Signal()

    def elaborate(self, platform: Platform):
        m = am.Module()

        for index in range(self.rom.length):
            m.d.comb += self.rom_view[index].eq(self.plain_rom[index])

        m.d.sync += self.operation.eq(self.rom_view[self.program_counter])
        m.d.sync += self.program_counter.eq(self.program_counter + 1)

        with m.If(self.operation == Operation.HALT):
            m.d.sync += self.is_halted.eq(True)
        with m.Else():
            m.d.sync += self.is_halted.eq(False)

        return m


def test():
    dut = Cpu()

    def bench():
        for index in range(dut.rom.length):
            print(f"{yield dut.rom_view[index]:02X} ", end="")

        while not (yield dut.is_halted):
            yield
            print(f"\npc: {yield dut.program_counter:02X} op: {yield dut.operation:02X}")
        print("Program halted")

    sim = Simulator(dut)
    sim.add_clock(1e-6)  # 1 MHz
    sim.add_sync_process(bench)
    with sim.write_vcd("cpu.vcd"):
        sim.run()
        print("Tests passed")


if __name__ == "__main__":
    test()
