;    nop
;start:
;    copy input r0
;    jz end
;    copy input r1
;    jz end
;    call exec
;    copy r2 output
;    jump start
;end:
;    halt
;
;exec:
;    sub r0 r1 r2
;    ret

    ; read in bytes
    copy #0xC0 r7
rtr_loop:
    cmp #0xD0 r7
    jz rtr_out
    copy input [r7]
    inc r7
    jump rtr_loop
rtr_out:

    ; parse cols
    copy #0 r5
    copy #0xC0 r7
pcs_loop:
    cmp #0xCF r7
    jz pcs_out
    push r5
    call parse_col
    pop r6
    add r5 r6 r5
    inc r7
    jump pcs_loop
pcs_out:
    copy r5 output
    halt

parse_col:
    push link

    copy #1 r0
    call get_highest_col
    copy r5 r1
    copy #-1 r0
    call get_highest_col
    min r1 r5 r1

    copy #0 r5
    cmp r1 [r7]
    js pc_out ; [r7] >= r1 TODO Double check this, TODO S and C flags doesn't work currently
    sub r1 [r7] r5
pc_out:
    pop link
    ret

get_highest_col:
    push r7

    copy #0 r5
ghc_loop:
    max r5 [r7] r5
    cmp r7 #0xC0
    jz ghc_out
    cmp r7 #0xCF
    jz ghc_out
    add r0 r7 r7
    jump ghc_loop
ghc_out:
    pop r7
    ret

    ; push #1
    ; push #2
    ; push #3

    ; copy #11 r0
    ; copy #22 r1
    ; copy #33 r2

    ; pop r0
    ; pop r1
    ; pop r2
