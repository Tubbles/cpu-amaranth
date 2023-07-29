#!/usr/bin/env python3

import amaranth as am
from amaranth.build import Platform
# from amaranth.lib import data
from amaranth.sim import Simulator
import os
import struct

from codes import Operation, Argument


class Cpu(am.Elaboratable):
    def __init__(self, rom_file="build/rom_file", word_size=8, addr_bus_width=8, ram_size=256):
        self.word_size = word_size
        bytes_in_word = int(word_size/8)

        self.hf = am.Signal()  # Halt flag
        self.cf = am.Signal()  # Carry flag
        self.zf = am.Signal()  # Zero flag
        self.sf = am.Signal()  # Signed flag
        self.of = am.Signal()  # Overflow flag
        self.iocf = am.Signal()  # Illegal opcode flag

        self.irf = am.Signal(reset=1)  # Input read flag
        self.owf = am.Signal()  # Output written flag

        # self.register_layout = data.ArrayLayout(am.unsigned(word_size), Argument._NUM_REGS)
        # self.registers = data.View(self.register_layout, am.Signal(word_size * Argument._NUM_REGS))
        # self.input = self.registers[Argument.INPUT]
        # self.output = self.registers[Argument.OUTPUT]
        # self.pc = self.registers[Argument.PC]
        # self.tick = self.registers[Argument.TICK]

        self.registers = am.Memory(width=word_size, depth=Argument._NUM_REGS)
        # self.input = self.registers[Argument.INPUT]
        # self.output = self.registers[Argument.OUTPUT]
        # self.pc = self.registers[Argument.PC]
        # self.tick = self.registers[Argument.TICK]

        plain_ram = []
        with open(rom_file, "rb") as ifs:
            ifs.seek(0, os.SEEK_END)
            self.rom_size = ifs.tell()
            ifs.seek(0)
            while ifs.tell() != self.rom_size:
                plain_ram.append(struct.unpack(f"{bytes_in_word}B", ifs.read(bytes_in_word))[0])

        # self.ram_layout = data.ArrayLayout(am.unsigned(word_size), ram_size + 6)
        # self.ram = data.View(self.ram_layout, am.Signal(word_size * (ram_size + 6)))

        self.ram_size = ram_size + 6
        self.ram = am.Memory(width=word_size, depth=self.ram_size, init=plain_ram)

    def elaborate(self, platform: Platform):
        m = am.Module()

        # # Load program
        # with m.If(self.tick == 0):
        #     for index in range(self.rom_size):
        #         m.d.comb += self.ram[index].eq(self.plain_ram[index])

        # Set up all signals
        m.d.sync += self.hf.eq(False)
        m.d.sync += self.registers[Argument.OUTPUT].eq(0)
        m.d.sync += self.irf.eq(0)
        m.d.sync += self.owf.eq(0)

        # ram_cache = []
        # for index in range(7):
        #     ram_cache.append(am.Signal(self.word_size))
        #     m.d.comb += ram_cache[-1].eq(self.ram[self.pc + index])

        operation = am.Signal(self.word_size)
        m.d.comb += operation.eq(self.ram[self.registers[Argument.PC]])

        result = am.Signal(self.word_size)
        result_location = am.Signal(2)
        m.d.comb += result_location.eq(3)

        # Read arguments
        args = []
        for index in range(3):
            args.append(am.Signal(self.word_size))
            with m.Switch(self.ram[self.registers[Argument.PC] + index * 2 + 1]):
                with m.Case(Argument.REG):
                    m.d.comb += args[index].eq(self.registers[self.ram[self.registers[Argument.PC] + index * 2 + 2]])
                    with m.If(self.ram[self.registers[Argument.PC] + index * 2 + 2] == Argument.INPUT):
                        m.d.sync += self.irf.eq(1)
                with m.Case(Argument.IMM):
                    m.d.comb += args[index].eq(self.ram[self.registers[Argument.PC] + index * 2 + 2])
                with m.Case(Argument.IND):
                    m.d.comb += args[index].eq(self.ram[self.registers[self.ram[self.registers[Argument.PC] + index * 2 + 2]]])
                with m.Case(Argument.RAM):
                    m.d.comb += args[index].eq(self.ram[self.ram[self.registers[Argument.PC] + index * 2 + 2]])
                with m.Default():
                    # m.d.sync += self.iocf.eq(True)
                    # m.d.sync += self.hf.eq(True)
                    pass

        # Parse operation
        with m.Switch(operation):
            with m.Case(Operation.HALT):
                m.d.sync += self.hf.eq(True)
            with m.Case(Operation.NOP):
                num_args = 0
                m.d.sync += self.registers[Argument.PC].eq(self.registers[Argument.PC] + num_args * 2 + 1)

            with m.Case(Operation.ACC):
                num_args = 0
                m.d.comb += result.eq(args[0] + args[1])
                m.d.comb += result_location.eq(1)
                m.d.sync += self.registers[Argument.PC].eq(self.registers[Argument.PC] + num_args * 2 + 5)
            with m.Case(Operation.ADD):
                num_args = 0
                m.d.comb += result.eq(args[0] + args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.registers[Argument.PC].eq(self.registers[Argument.PC] + num_args * 2 + 7)
            with m.Case(Operation.SUB):
                num_args = 0
                m.d.comb += result.eq(args[0] - args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.registers[Argument.PC].eq(self.registers[Argument.PC] + num_args * 2 + 7)

            with m.Case(Operation.INC):
                num_args = 0
                m.d.comb += result.eq(args[0] + 1)
                m.d.comb += result_location.eq(0)
                m.d.sync += self.registers[Argument.PC].eq(self.registers[Argument.PC] + num_args * 2 + 3)
            with m.Case(Operation.DEC):
                num_args = 0
                m.d.comb += result.eq(args[0] - 1)
                m.d.comb += result_location.eq(0)
                m.d.sync += self.registers[Argument.PC].eq(self.registers[Argument.PC] + num_args * 2 + 3)

            with m.Case(Operation.CPY):
                num_args = 0
                m.d.comb += result.eq(args[0])
                m.d.comb += result_location.eq(1)
                m.d.sync += self.registers[Argument.PC].eq(self.registers[Argument.PC] + num_args * 2 + 5)

            with m.Case(Operation.JMP):
                num_args = 0
                m.d.comb += result.eq(args[0])
                m.d.sync += self.registers[Argument.PC].eq(result)
            with m.Case(Operation.RJMP):
                num_args = 0
                m.d.comb += result.eq(args[0])
                m.d.sync += self.registers[Argument.PC].eq(self.registers[Argument.PC] + result)

            with m.Default():
                m.d.sync += self.iocf.eq(True)
                m.d.sync += self.hf.eq(True)
                pass

        # Write result
        for index in range(3):
            with m.If(result_location == index):
                with m.Switch(self.ram[self.registers[Argument.PC] + index * 2 + 1]):
                    with m.Case(Argument.REG):
                        m.d.sync += self.registers[self.ram[self.registers[Argument.PC] + index * 2 + 2]].eq(result)
                        with m.If(self.ram[self.registers[Argument.PC] + index * 2 + 2] == Argument.OUTPUT):
                            m.d.sync += self.owf.eq(1)
                    with m.Case(Argument.IND):
                        m.d.sync += self.ram[self.registers[self.ram[self.registers[Argument.PC] + index * 2 + 2]]].eq(result)
                    with m.Case(Argument.RAM):
                        m.d.sync += self.ram[self.ram[self.registers[Argument.PC] + index * 2 + 2]].eq(result)
                    with m.Default():
                        m.d.sync += self.iocf.eq(True)
                        m.d.sync += self.hf.eq(True)
                        pass

        # with m.If(self.irf):
        #     m.d.sync += self.registers[Argument.INPUT].eq(0)

        m.d.sync += self.registers[Argument.TICK].eq(self.registers[Argument.TICK] + 1)
        return m


def test(interactive):
    dut = Cpu()

    def bench():
        inputs = [
            0xB4, 0xF6,
            0xAF, 0x70,
            0x5C, 0xC7,
            0xCA, 0x15,
            0x1A, 0x2A,
            0x14, 0x29,
            0xED, 0xE0,
            0x47, 0x66,
            0xB7, 0x7C,
            0xC5, 0xDD,
            0xE1, 0xEA,
        ]

        outputs = [
            0xAA,
            0x1F,
            0x23,
            0xDF,
            0x44,
            0x3D,
            0xCD,
            0xAD,
            0x33,
            0xA2,
            0xCB,
        ]

        debug = interactive

        # yield dut.registers[Argument.INPUT].eq(inputs.pop(0))

        while not (yield dut.hf) or debug:

            if (yield dut.irf):
                yield dut.registers[Argument.INPUT].eq(inputs.pop(0))

            if (yield dut.owf):
                print(f"Read output: {yield dut.registers[Argument.OUTPUT]:02X}")
                # assert (yield dut.registers[Argument.OUTPUT] == outputs.pop(0))

            print(f"tick {yield dut.registers[Argument.TICK]:02X}: ", end="")
            print(f"pc: {yield dut.registers[Argument.PC]:02X} ", end="")
            op = bytearray(7)
            op[0] = yield dut.ram[dut.registers[Argument.PC] + 0]
            op[1] = yield dut.ram[dut.registers[Argument.PC] + 1]
            op[2] = yield dut.ram[dut.registers[Argument.PC] + 2]
            op[3] = yield dut.ram[dut.registers[Argument.PC] + 3]
            op[4] = yield dut.ram[dut.registers[Argument.PC] + 4]
            op[5] = yield dut.ram[dut.registers[Argument.PC] + 5]
            op[6] = yield dut.ram[dut.registers[Argument.PC] + 6]
            opstring = Operation.decode(op)
            print(f"next_op: {opstring}   ", end="")
            print(f"hf: {yield dut.hf} ", end="")
            print(f"cf: {yield dut.cf} ", end="")
            print(f"zf: {yield dut.zf} ", end="")
            print(f"sf: {yield dut.sf} ", end="")
            print(f"of: {yield dut.of} ", end="")
            print(f"iocf: {yield dut.iocf} ", end="")
            print(f"irf: {yield dut.irf} ", end="")
            print(f"owf: {yield dut.owf}   ", end="")
            for index in range(Argument._NUM_REGS):
                if index != 0 and index % 4 == 0:
                    print(" ", end="")
                print(f"r{index}: {yield dut.registers[index]:02X} ", end="")
            print("")
            if debug:
                try:
                    cmd = input("> ")
                except (EOFError, KeyboardInterrupt):
                    print()
                    return
                if cmd == "dump":
                    print(f"RAM dump:\n      0  1  2  3  4  5  6  7   8  9  A  B  C  D  E  F\n{0:03X}: ", end="")
                    for index in range(dut.ram_size):
                        if index != 0 and index % 16 == 0:
                            print(f"\n{index:03X}: ", end="")
                        elif index != 0 and index % 8 == 0:
                            print(" ", end="")
                        print(f"{yield dut.ram[index]:02X} ", end="")
                    print()
                elif cmd == "q":
                    return
                elif cmd == "r":
                    debug = False
                else:
                    if not (yield dut.hf):
                        yield

            else:
                if not (yield dut.hf):
                    yield

        print("Program halted")
        # print(f"tick {yield dut.registers[Argument.TICK]:02X}: ", end="")
        # print(f"pc: {yield dut.registers[Argument.PC]:02X} ", end="")
        # op = [0] * 7
        # op[0] = yield dut.ram[dut.registers[Argument.PC] + 0]
        # op[1] = yield dut.ram[dut.registers[Argument.PC] + 1]
        # op[2] = yield dut.ram[dut.registers[Argument.PC] + 2]
        # op[3] = yield dut.ram[dut.registers[Argument.PC] + 3]
        # op[4] = yield dut.ram[dut.registers[Argument.PC] + 4]
        # op[5] = yield dut.ram[dut.registers[Argument.PC] + 5]
        # op[6] = yield dut.ram[dut.registers[Argument.PC] + 6]
        # opstring = Operation.decode(bytearray(op))
        # print(f"op: {opstring}   ", end="")
        # print(f"hf: {yield dut.hf} ", end="")
        # print(f"cf: {yield dut.cf} ", end="")
        # print(f"zf: {yield dut.zf} ", end="")
        # print(f"sf: {yield dut.sf} ", end="")
        # print(f"of: {yield dut.of} ", end="")
        # print(f"iocf: {yield dut.iocf}   ", end="")
        # for index in range(Argument._NUM_REGS):
        #     if index != 0 and index % 4 == 0:
        #         print(" ", end="")
        #     print(f"r{index}: {yield dut.registers[index]:02X} ", end="")
        # print("")

        # Print RAM contents
        print(f"RAM dump:\n      0  1  2  3  4  5  6  7   8  9  A  B  C  D  E  F\n{0:03X}: ", end="")
        for index in range(dut.ram_size):
            if index != 0 and index % 16 == 0:
                print(f"\n{index:03X}: ", end="")
            elif index != 0 and index % 8 == 0:
                print(" ", end="")
            print(f"{yield dut.ram[index]:02X} ", end="")
        print()

    sim = Simulator(dut)
    sim.add_clock(1e-6)  # 1 MHz
    sim.add_sync_process(bench)
    with sim.write_vcd("cpu.vcd"):
        sim.run()


if __name__ == "__main__":
    # test(False)
    test(True)
