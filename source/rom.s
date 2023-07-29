    nop
start:
    cpy input r1
    add input r1 output
    jmp start
end:
    halt
