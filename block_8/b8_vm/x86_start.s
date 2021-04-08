.globl main
format: .asciz "%x\n"
.text
; push_di: ; esp -= 8 total
;     push %di ; esp -= 2
;     pushl $0 ; esp -= 4
;     pushw $0 ; esp -= 2
;     ret
push_di: ; esp -= 16 total
    push %di ; esp -= 2
    sub $14 %esp ; esp -= 14
    ret
push_si:
    push %si
    sub $14 %esp
    ret
push_bx:
    push %bx
    sub $14 esp
    ret
push_bp:
    push %bp
    sub $14 %esp
    ret
pop_di: ; esp += 16 total
    add $14 %esp ; esp += 14
    pop %di ; esp += 2
    ret
pop_si:
    add $14 %esp
    pop %si
    ret
pop_bx:
    add $14 %esp
    pop %bx
    ret
pop_bp:
    add $14 %esp
    pop %bp
    ret
push_const: ; uses ecx (normally call-clobbered)
    pushw %ecx ; esp -= 2
    sub $14 %esp ; esp -= 14
b8_vm_printf:
    ; esp - 8 should be a multiple of 16
    push %si ; preserve value of si (i.e., Block-8 r1). esp -= 2
    sub $6 %esp ; esp -= 6
    movzwl %di, %esi
    lea format, %di
    xor %ax, %ax
    call printf
    pop %si
    ret
main:
