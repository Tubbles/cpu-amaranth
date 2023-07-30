#!/usr/bin/env python3

import amaranth as am
from amaranth.build import Platform
# from amaranth.lib import data
from amaranth.sim import Simulator
import os
import struct

from codes import Operation, Argument


class C:
    RESET = '\033[0m'

    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    DEFAULT = '\033[39m'

    BBLACK = '\033[90m'
    BRED = '\033[91m'
    BGREEN = '\033[92m'
    BYELLOW = '\033[93m'
    BBLUE = '\033[94m'
    BMAGENTA = '\033[95m'
    BCYAN = '\033[96m'
    BWHITE = '\033[97m'

    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    BG_DEFAULT = '\033[49m'

    BG_BBLACK = '\033[100m'
    BG_BRED = '\033[101m'
    BG_BGREEN = '\033[102m'
    BG_BYELLOW = '\033[103m'
    BG_BBLUE = '\033[104m'
    BG_BMAGENTA = '\033[105m'
    BG_BCYAN = '\033[106m'
    BG_BWHITE = '\033[107m'


CFI = 0  # Carry flag signal index
OFI = 1  # Overflow flag signal index
SFI = 2  # Signed flag signal index
ZFI = 3  # Zero flag signal index

CF = 1 << CFI  # Carry flag mask
OF = 1 << OFI  # Overflow flag mask
SF = 1 << SFI  # Signed flag mask
ZF = 1 << ZFI  # Zero flag mask

NUM_ARGS_0 = 0 * 2 + 1
NUM_ARGS_1 = 1 * 2 + 1
NUM_ARGS_2 = 2 * 2 + 1
NUM_ARGS_3 = 3 * 2 + 1


class Cpu(am.Elaboratable):
    def f(self, index):
        return self.registers[Argument.STATUS][index]

    def c(self):
        return self.registers[Argument.STATUS][CFI]

    def o(self):
        return self.registers[Argument.STATUS][OFI]

    def s(self):
        return self.registers[Argument.STATUS][SFI]

    def z(self):
        return self.registers[Argument.STATUS][ZFI]

    def r(self, index):
        return self.registers[index]

    def r0(self):
        return self.registers[Argument.R0]

    def r1(self):
        return self.registers[Argument.R1]

    def r2(self):
        return self.registers[Argument.R2]

    def r3(self):
        return self.registers[Argument.R3]

    def r4(self):
        return self.registers[Argument.R4]

    def r5(self):
        return self.registers[Argument.R5]

    def r6(self):
        return self.registers[Argument.R6]

    def r7(self):
        return self.registers[Argument.R7]

    def status(self):
        return self.registers[Argument.STATUS]

    def link(self):
        return self.registers[Argument.LINK]

    def input(self):
        return self.registers[Argument.INPUT]

    def output(self):
        return self.registers[Argument.OUTPUT]

    def pc(self):
        return self.registers[Argument.PC]

    def sp(self):
        return self.registers[Argument.SP]

    def tick(self):
        return self.registers[Argument.TICK]

    def __init__(self, rom_file="build/rom_file", word_size=8, addr_bus_width=8, ram_size=256):
        self.word_size = word_size
        self.ram_size = ram_size + 6

        bytes_in_word = int(word_size/8)

        # Set up internal flags
        self.hf = am.Signal()  # Halt flag
        self.iocf = am.Signal()  # Illegal opcode flag
        self.irf = am.Signal(reset=1)  # Input read flag
        self.owf = am.Signal()  # Output written flag

        # Set up registers
        self.registers = am.Memory(width=word_size, depth=Argument._NUM_REGS)
        self.sp().reset = ram_size - 1

        # Set up RAM
        plain_ram = []
        with open(rom_file, "rb") as ifs:
            ifs.seek(0, os.SEEK_END)
            self.rom_size = ifs.tell()
            ifs.seek(0)
            while ifs.tell() != self.rom_size:
                plain_ram.append(struct.unpack(f"{bytes_in_word}B", ifs.read(bytes_in_word))[0])

        self.ram = am.Memory(width=word_size, depth=self.ram_size, init=plain_ram)

    def elaborate(self, platform: Platform):
        m = am.Module()

        # Set up all signals
        m.d.sync += self.hf.eq(False)
        m.d.sync += self.output().eq(0)
        m.d.sync += self.irf.eq(0)
        m.d.sync += self.owf.eq(0)

        operation = am.Signal(self.word_size)
        m.d.comb += operation.eq(self.ram[self.pc()])

        result = am.Signal(self.word_size)
        result_location = am.Signal(2)
        m.d.comb += result_location.eq(3)
        do_flags = am.Signal(4)

        # Read arguments
        args = []
        for index in range(3):
            args.append(am.Signal(self.word_size))
            with m.Switch(self.ram[self.pc() + index * 2 + 1]):
                with m.Case(Argument.REG):
                    m.d.comb += args[index].eq(self.registers[self.ram[self.pc() + index * 2 + 2]])
                    with m.If(self.ram[self.pc() + index * 2 + 2] == Argument.INPUT):
                        m.d.sync += self.irf.eq(1)
                with m.Case(Argument.IMM):
                    m.d.comb += args[index].eq(self.ram[self.pc() + index * 2 + 2])
                with m.Case(Argument.IND):
                    m.d.comb += args[index].eq(self.ram[self.registers[self.ram[self.pc() + index * 2 + 2]]])
                with m.Case(Argument.RAM):
                    m.d.comb += args[index].eq(self.ram[self.ram[self.pc() + index * 2 + 2]])
                with m.Default():
                    # m.d.sync += self.iocf.eq(True)
                    # m.d.sync += self.hf.eq(True)
                    pass

        # Parse operation
        with m.Switch(operation):
            with m.Case(Operation.HALT):
                m.d.sync += self.hf.eq(True)
            with m.Case(Operation.NOP):
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_0)

            with m.Case(Operation.AND):
                m.d.comb += result.eq(args[0] & args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_3)
                m.d.comb += do_flags.eq(SF | ZF)
            with m.Case(Operation.OR):
                m.d.comb += result.eq(args[0] | args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_3)
                m.d.comb += do_flags.eq(SF | ZF)
            with m.Case(Operation.XOR):
                m.d.comb += result.eq(args[0] ^ args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_3)
                m.d.comb += do_flags.eq(SF | ZF)

            with m.Case(Operation.NOT):
                m.d.comb += result.eq(~args[0])
                m.d.comb += result_location.eq(1)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_2)
                m.d.comb += do_flags.eq(SF | ZF)
            with m.Case(Operation.NEG):
                m.d.comb += result.eq(-args[0])
                m.d.comb += result_location.eq(1)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_2)
                m.d.comb += do_flags.eq(SF | ZF)
            with m.Case(Operation.ABS):
                m.d.comb += result.eq(abs(args[0]))
                m.d.comb += result_location.eq(1)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_2)
                m.d.comb += do_flags.eq(SF | ZF)

            with m.Case(Operation.ADD):
                m.d.comb += result.eq(args[0] + args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_3)
                m.d.comb += do_flags.eq(CF | OF | SF | ZF)
            with m.Case(Operation.SUB):
                m.d.comb += result.eq(args[0] - args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_3)
                m.d.comb += do_flags.eq(CF | OF | SF | ZF)

            with m.Case(Operation.MULL):
                m.d.comb += result.eq(args[0] * args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_3)
                m.d.comb += do_flags.eq(SF | ZF)
            with m.Case(Operation.MULH):
                m.d.comb += result.eq((args[0] * args[1]) >> self.word_size)
                m.d.comb += result_location.eq(2)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_3)
                m.d.comb += do_flags.eq(SF | ZF)

            with m.Case(Operation.DIV):
                m.d.comb += result.eq(args[0] // args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_3)
                m.d.comb += do_flags.eq(SF | ZF)
            with m.Case(Operation.MOD):
                m.d.comb += result.eq(args[0] % args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_3)
                m.d.comb += do_flags.eq(SF | ZF)

            with m.Case(Operation.CMP):
                m.d.comb += result.eq(args[0] % args[1])
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_2)
                m.d.comb += do_flags.eq(CF | OF | SF | ZF)

            with m.Case(Operation.INC):
                m.d.comb += result.eq(args[0] + 1)
                m.d.comb += result_location.eq(0)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_1)
                m.d.comb += do_flags.eq(CF | OF | SF | ZF)
            with m.Case(Operation.DEC):
                m.d.comb += result.eq(args[0] - 1)
                m.d.comb += result_location.eq(0)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_1)
                m.d.comb += do_flags.eq(CF | OF | SF | ZF)

            with m.Case(Operation.MIN):
                with m.If(args[0] < args[1]):
                    m.d.comb += result.eq(args[0])
                with m.Else():
                    m.d.comb += result.eq(args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_3)
                m.d.comb += do_flags.eq(SF | ZF)
            with m.Case(Operation.MAX):
                with m.If(args[0] > args[1]):
                    m.d.comb += result.eq(args[0])
                with m.Else():
                    m.d.comb += result.eq(args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_3)
                m.d.comb += do_flags.eq(SF | ZF)

            with m.Case(Operation.ASHR):
                m.d.comb += result.eq(args[0].as_signed() >> args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_3)
                m.d.comb += do_flags.eq(SF | ZF)
            with m.Case(Operation.SHR):
                m.d.comb += result.eq(args[0].as_unsigned() >> args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_3)
                m.d.comb += do_flags.eq(SF | ZF)
            with m.Case(Operation.SHL):
                m.d.comb += result.eq(args[0] << args[1])
                m.d.comb += result_location.eq(2)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_3)
                m.d.comb += do_flags.eq(SF | ZF)

            with m.Case(Operation.COPY):
                m.d.comb += result.eq(args[0])
                m.d.comb += result_location.eq(1)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_2)
                m.d.comb += do_flags.eq(SF | ZF)

            with m.Case(Operation.JUMP):
                m.d.comb += result.eq(args[0])
                m.d.sync += self.pc().eq(result)
            with m.Case(Operation.JC):
                m.d.comb += result.eq(args[0])
                with m.If(self.c()):
                    m.d.sync += self.pc().eq(result)
                with m.Else():
                    m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_1)
            with m.Case(Operation.JNC):
                m.d.comb += result.eq(args[0])
                with m.If(~self.c()):
                    m.d.sync += self.pc().eq(result)
                with m.Else():
                    m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_1)
            with m.Case(Operation.JO):
                m.d.comb += result.eq(args[0])
                with m.If(self.o()):
                    m.d.sync += self.pc().eq(result)
                with m.Else():
                    m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_1)
            with m.Case(Operation.JNO):
                m.d.comb += result.eq(args[0])
                with m.If(~self.o()):
                    m.d.sync += self.pc().eq(result)
                with m.Else():
                    m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_1)
            with m.Case(Operation.JS):
                m.d.comb += result.eq(args[0])
                with m.If(self.s()):
                    m.d.sync += self.pc().eq(result)
                with m.Else():
                    m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_1)
            with m.Case(Operation.JNS):
                m.d.comb += result.eq(args[0])
                with m.If(~self.s()):
                    m.d.sync += self.pc().eq(result)
                with m.Else():
                    m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_1)
            with m.Case(Operation.JZ):
                m.d.comb += result.eq(args[0])
                with m.If(self.z()):
                    m.d.sync += self.pc().eq(result)
                with m.Else():
                    m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_1)
            with m.Case(Operation.JNZ):
                m.d.comb += result.eq(args[0])
                with m.If(~self.z()):
                    m.d.sync += self.pc().eq(result)
                with m.Else():
                    m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_1)

            with m.Case(Operation.CALL):
                m.d.sync += self.link().eq(self.pc() + NUM_ARGS_1)
                m.d.comb += result.eq(args[0])
                m.d.sync += self.pc().eq(result)
            with m.Case(Operation.RET):
                m.d.comb += result.eq(self.link())
                m.d.sync += self.pc().eq(result)

            with m.Case(Operation.PUSH):
                m.d.sync += self.ram[self.sp()].eq(args[0])
                m.d.sync += self.sp().eq(self.sp() - 1)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_1)
            with m.Case(Operation.POP):
                m.d.sync += self.sp().eq(self.sp() + 1)
                m.d.comb += result.eq(self.ram[self.sp()] + 1)
                m.d.comb += result_location.eq(0)
                m.d.sync += self.pc().eq(self.pc() + NUM_ARGS_1)

            with m.Default():
                m.d.sync += self.iocf.eq(True)
                m.d.sync += self.hf.eq(True)
                pass

        # Write result
        for index in range(3):
            with m.If(result_location == index):
                with m.Switch(self.ram[self.pc() + index * 2 + 1]):
                    with m.Case(Argument.REG):
                        m.d.sync += self.registers[self.ram[self.pc() + index * 2 + 2]].eq(result)
                        with m.If(self.ram[self.pc() + index * 2 + 2] == Argument.OUTPUT):
                            m.d.sync += self.owf.eq(1)
                    with m.Case(Argument.IND):
                        m.d.sync += self.ram[self.registers[self.ram[self.pc() + index * 2 + 2]]].eq(result)
                    with m.Case(Argument.RAM):
                        m.d.sync += self.ram[self.ram[self.pc() + index * 2 + 2]].eq(result)
                    with m.Default():
                        m.d.sync += self.iocf.eq(True)
                        m.d.sync += self.hf.eq(True)
                        pass

        # Set flags
        with m.If(do_flags[CFI] == 1):
            pass
            # with m.If(result[0] == 1):
            #     m.d.sync += self.s().eq(1)
            # with m.Else():
            #     m.d.sync += self.s().eq(0)
        with m.If(do_flags[OFI] == 1):
            pass
            # with m.If(result[0] == 1):
            #     m.d.sync += self.s().eq(1)
            # with m.Else():
            #     m.d.sync += self.s().eq(0)
        with m.If(do_flags[SFI] == 1):
            with m.If(result[0] == 1):
                m.d.sync += self.s().eq(1)
            with m.Else():
                m.d.sync += self.s().eq(0)
        with m.If(do_flags[ZFI] == 1):
            with m.If(result == 0):
                m.d.sync += self.z().eq(1)
            with m.Else():
                m.d.sync += self.z().eq(0)

        m.d.sync += self.tick().eq(self.tick() + 1)
        return m


def test(interactive):
    dut = Cpu()

    def bench():
        # inputs = [
        #     0xB4, 0xF6,
        #     0xAF, 0x70,
        #     0x5C, 0xC7,
        #     0xCA, 0x15,
        #     0x1A, 0x2A,
        #     0x14, 0x29,
        #     0xED, 0xE0,
        #     0x47, 0x66,
        #     0xB7, 0x7C,
        #     0xC5, 0xDD,
        #     0xE1, 0xEA,
        # ]

        # outputs = [
        #     190,
        #     63,
        #     149,
        #     181,
        #     240,
        #     235,
        #     13,
        #     225,
        #     59,
        #     232,
        #     247,
        # ]

        inputs = [4, 6, 1, 4, 6, 5, 1, 4, 1, 2, 6, 5, 6, 1, 4, 2, ]
        outputs = [5 + 2 + 1 + 5 + 2 + 5 + 4 + 1 + 3, ]

        debug = interactive

        while not (yield dut.hf) or debug:

            # Send inputs
            if (yield dut.irf):
                next = inputs.pop(0) if len(inputs) > 0 else 0
                yield dut.input().eq(next)

            # Receive outputs
            if (yield dut.owf):
                if len(outputs) > 0:
                    print(f"Read output: {yield dut.output():02X}")
                    assert (yield dut.output() == outputs.pop(0))
                else:
                    print(f"Unexpected output: {yield dut.output():02X}")

            # Print flags
            print(f"{C.BWHITE}h: {yield dut.hf} ", end="")
            print(f"{C.BYELLOW}c: {yield dut.c()} ", end="")
            print(f"{C.BYELLOW}o: {yield dut.o()} ", end="")
            print(f"{C.BBLUE}s: {yield dut.s()} ", end="")
            print(f"{C.BBLUE}z: {yield dut.z()} ", end="")
            print(f"{C.BWHITE}ioc: {yield dut.iocf} ", end="")
            print(f"{C.BWHITE}ir: {yield dut.irf} ", end="")
            print(f"{C.BWHITE}ow: {yield dut.owf}   ", end="")

            # Print registers
            acolor = False
            color = C.BWHITE if acolor else C.BYELLOW
            for index in range(Argument._NUM_REGS):
                if index != 0 and index % 4 == 0:
                    print(" ", end="")
                if index % 2 == 0:
                    acolor = not acolor
                    color = C.BWHITE if acolor else C.BYELLOW
                print(f"{color}{Argument.lookup(index).lower()}: {yield dut.registers[index]:02X}{C.RESET} ", end="")

            # Print next operation
            op = bytearray(7)
            op[0] = yield dut.ram[dut.pc() + 0]
            op[1] = yield dut.ram[dut.pc() + 1]
            op[2] = yield dut.ram[dut.pc() + 2]
            op[3] = yield dut.ram[dut.pc() + 3]
            op[4] = yield dut.ram[dut.pc() + 4]
            op[5] = yield dut.ram[dut.pc() + 5]
            op[6] = yield dut.ram[dut.pc() + 6]
            opstring = Operation.decode(op)
            print(f"  next_op: {opstring}")

            if debug:
                try:
                    cmd = input("> ")
                except EOFError:
                    print()
                    return

                if cmd == "dump":
                    print(f"RAM dump:\n      0  1  2  3  4  5  6  7   8  9  A  B  C  D  E  F\n{0:03X}: ", end="")
                    acolor = False
                    color = C.BWHITE if acolor else C.BYELLOW
                    for index in range(dut.ram_size):
                        if index % 2 == 0:
                            acolor = not acolor
                            color = C.BWHITE if acolor else C.BYELLOW
                        if index != 0 and index % 16 == 0:
                            print(f"\n{index:03X}: ", end="")
                        elif index != 0 and index % 8 == 0:
                            print(" ", end="")
                        print(f"{color}{yield dut.ram[index]:02X}{C.RESET} ", end="")
                    print()

                elif cmd == "q":
                    return

                elif cmd == "r":
                    debug = False
                    if not (yield dut.hf):
                        yield
                        if (yield dut.hf):
                            print("Program halted")

                else:
                    if not (yield dut.hf):
                        yield
                        if (yield dut.hf):
                            print("Program halted")

            else:
                if not (yield dut.hf):
                    yield

        print("Program halted")

        # Print RAM contents
        print(f"RAM dump:\n      0  1  2  3  4  5  6  7   8  9  A  B  C  D  E  F\n{0:03X}: ", end="")
        acolor = False
        color = C.BWHITE if acolor else C.BYELLOW
        for index in range(dut.ram_size):
            if index % 2 == 0:
                acolor = not acolor
                color = C.BWHITE if acolor else C.BYELLOW
            if index != 0 and index % 16 == 0:
                print(f"\n{index:03X}: ", end="")
            elif index != 0 and index % 8 == 0:
                print(" ", end="")
            print(f"{color}{yield dut.ram[index]:02X}{C.RESET} ", end="")
        print()

        assert len(inputs) == 0 and len(outputs) == 0

    sim = Simulator(dut)
    sim.add_clock(1e-6)  # 1 MHz
    sim.add_sync_process(bench)
    with sim.write_vcd("cpu.vcd"):
        sim.run()
        print("All tests passed")


if __name__ == "__main__":
    # test(False)
    test(True)
