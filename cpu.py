#!/usr/bin/env python3

import amaranth as am
from amaranth.build import Platform
from amaranth.lib import data
from amaranth.sim import Simulator
import os
import struct
# from typing import Enum


class Cpu(am.Elaboratable):
    def __init__(self, rom_file="rom_file", word_size=8, addr_bus_width=8, num_aux_regs=8):
        bytes_in_word = int(word_size/8)

        # Params
        self.rom = []
        with open(rom_file, "rb") as ifs:
            ifs.seek(0, os.SEEK_END)
            size = ifs.tell()
            self.rom = data.ArrayLayout(am.unsigned(word_size), size)
            ifs.seek(0)
            index = 0
            while ifs.tell() != size:
                self.rom[index] = struct.unpack(f"{bytes_in_word}B", ifs.read(bytes_in_word))[0]
                index += 1

        self.pc = am.Signal(addr_bus_width)
        self.op = am.Signal(word_size)
        self.regs = [am.Signal(word_size)] * num_aux_regs
        self.halted = am.Signal()

    def elaborate(self, platform: Platform):
        m = am.Module()

        m.d.sync += self.op.eq(self.rom[self.pc])
        m.d.sync += self.pc.eq(self.pc + 1)

        # with m.If(self.pc == )

        # m.d.sync += self.regs[0].eq(self.limit)
        # for index in range(len(self.rom)):
        #     m.d.sync += self.rom[index]

        m.d.sync += self.halted.eq(True)

        return m


def test():
    dut = Cpu()

    def bench():
        while not (yield dut.halted):
            yield
            for index in range(len(dut.rom)):
                print(f"{yield dut.rom[index]:02X} ", end="")
            print(f"\npc: {yield dut.pc} op: {yield dut.op}")

    sim = Simulator(dut)
    sim.add_clock(1e-6)  # 1 MHz
    sim.add_sync_process(bench)
    with sim.write_vcd("up_counter.vcd"):
        sim.run()
        print("Tests passed")


if __name__ == "__main__":
    test()
