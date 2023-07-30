#!/usr/bin/env python3

import struct


class MyEnum:
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


class Argument(MyEnum):
    # Register operands
    R0 = 0
    R1 = 1
    R2 = 2
    R3 = 3
    R4 = 4
    R5 = 5
    R6 = 6
    R7 = 7
    STATUS = 8
    LINK = 9
    INPUT = 10
    OUTPUT = 11
    PC = 12
    SP = 13
    TICK = 14

    # Addressing modes
    REG = 15  # r1
    IMM = 16  # #123
    IND = 17  # [r1]
    RAM = 18  # [#123]
#    IMM_REL = 17  # #+123, used for jmp

    _NUM_REGS = TICK + 1


class Operation(MyEnum):
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
                out = f"#{imm:02X} "
            elif mode == "IND":
                out = f"[{reg}] "
            elif mode == "RAM":
                out = f"[#{imm:02X}] "
            return out

        out = f"{Operation.lookup(struct.unpack('B', bytebuf[0:1])[0])} "
        out += decode_arg(bytebuf, 1)
        out += decode_arg(bytebuf, 3)
        out += decode_arg(bytebuf, 5)

        return out

    HALT = 0
    NOP = 1

    AND = 2  # a1/2 = a0 & a1 (sz)
    OR = 3  # a1/2 = a0 | a1 (sz)
    XOR = 4  # a1/2 = a0 ^ a1 (sz)

    NOT = 5  # a0/1 = ~a0 (sz)
    NEG = 6  # a0/1 = -a0 (sz)
    ABS = 7  # a0/1 = |a0| (sz)

    ADD = 8  # a1/2 = a0 + a1 (cosz)
    SUB = 9  # a1/2 = a0 - a1 (cosz)

    MULL = 10  # a1/2 = a0 * a1 (sz)
    MULH = 11  # a1/2 = (a0 * a1) >> bw (sz)

    DIV = 12  # a1/2 = a0 / a1 (sz)
    MOD = 13  # a1/2 = a0 % a1 (sz)

    CMP = 14  # a0 - a1 (cosz)
#   CLC = 5  # (c = 0)
#   SEC = 6  # (c = 1)
#   CLO = 11  # (o = 0)
#   SEO = 12  # (o = 1)
#   CLS = 9  # (s = 0)
#   SES = 10  # (s = 1)
#   CLZ = 7  # (z = 0)
#   SEZ = 8  # (z = 1)

    INC = 15  # a0 += 1 (cosz)
    DEC = 16  # a0 -= 1 (cosz)

    MIN = 17  # a1/2 = a0 if a0 < a1 else a1 (sz)
    MAX = 18  # a1/2 = a0 if a0 > a1 else a1 (sz)

    ASHR = 19  # a1/2 = a0 >> a1 (copies high bit) (sz)
    SHR = 20  # a1/2 = a0 >> a1 (shift in 0's) (sz)
    SHL = 21  # a1/2 = a0 << a1 (shift in 0's) (sz)

    COPY = 22  # a1 = a0 (sz)
#   COPY = CPY

    JUMP = 23  # pc = a0 (+pc)
    JC = 24  # pc = a0 (+pc) if c
    JNC = 25  # pc = a0 (+pc) if !c
    JO = 26  # pc = a0 (+pc) if o
    JNO = 27  # pc = a0 (+pc) if !o
    JS = 28  # pc = a0 (+pc) if s
    JNS = 29  # pc = a0 (+pc) if !s
    JZ = 30  # pc = a0 (+pc) if z
    JNZ = 31  # pc = a0 (+pc) if !z

#   JUMP = JMP
#   JEQ = JZ
#   JNEQ = JNZ

    CALL = 32  # link = pc, pc = a0
    RET = 33  # pc = link

    PUSH = 34  # push a0, sp -= 1
    POP = 35  # sp += 1, a0 = pop


if __name__ == "__main__":
    pass
