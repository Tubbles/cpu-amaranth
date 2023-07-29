#!/usr/bin/env python3

import struct


class Argument:
    @classmethod
    def members(cls):
        return [attr for attr in dir(cls) if not callable(getattr(cls, attr)) and not attr.startswith("_")]

    @classmethod
    def get(cls, name):
        return getattr(cls, name)

    @classmethod
    def lookup(cls, number):
        for mem in cls.members():
            if cls.get(mem) == number:
                return mem
        return f"{number}"

    # Register operands
    R0 = 0
    R1 = 1
    R2 = 2
    R3 = 3
    INPUT = 4
    OUTPUT = 5
    PC = 6
    TICK = 7
    R4 = INPUT
    R5 = OUTPUT
    R6 = PC
    R7 = TICK

    # Addressing modes
    REG = 8  # r1
    IMM = 9  # #123
    IND = 10  # [r1]
    RAM = 11  # [#123]

    _NUM_REGS = R7 + 1


class Operation:
    @classmethod
    def members(cls):
        return [attr for attr in dir(cls) if not callable(getattr(cls, attr)) and not attr.startswith("_")]

    @classmethod
    def get(cls, name):
        return getattr(cls, name)

    @classmethod
    def lookup(cls, number):
        for mem in cls.members():
            if cls.get(mem) == number:
                return mem
        return f"{number}"

    @staticmethod
    def decode(bytebuf):
        def decode_arg(bytebuf, offset):
            mode = Argument.lookup(struct.unpack('B', bytebuf[offset:offset+1])[0])
            reg = Argument.lookup(struct.unpack('B', bytebuf[offset+1:offset+2])[0])
            imm = bytebuf[offset+1]
            out = ""
            if mode == "REG":
                out = f"{reg} "
            elif mode == "IMM":
                out = f"#{imm} "
            elif mode == "IND":
                out = f"[{reg}] "
            elif mode == "RAM":
                out = f"[#{imm}] "
            return out

        out = f"{Operation.lookup(struct.unpack('B', bytebuf[0:1])[0])} "
        out += decode_arg(bytebuf, 1)
        out += decode_arg(bytebuf, 3)
        out += decode_arg(bytebuf, 5)

        return out

    HALT = 0
    NOP = 1

    ACC = 2  # a1 += a0
    ADD = 3  # a2 = a0 + a1
    SUB = 4  # a2 = a0 - a1

    INC = 5  # a0 += 1
    DEC = 6  # a0 -= 1

    SHR = 7  # a0 >>= a1 (shift in 0's)
    SHL = 8  # a0 <<= a1 (shift in 0's)
    ASHR = 9  # a0 >>= a1 (shift in 1's)

    CPY = 10  # a1 = a0

    JMP = 11  # pc = a0
    RJMP = 12  # pc += a0


if __name__ == "__main__":
    pass
