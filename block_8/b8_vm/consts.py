INSTRUCTION_MODE = "instruction_mode"
ARGUMENT_MODE = "argument_mode"

INSTRUCTION_CODES = (
    "no_op_pause",  # 0
    "move",  # 1
    "push_pop",  # 2
    "compare",  # 3
    "add",  # 4
    "subtract",  # 5
    "multiply",  # 6
    "divide",  # 7
    "bit-and",  # 8
    "bit-or",  # 9
    "bit-xor",  # 10
    "bit-not",  # 11
    "left-shift",  # 12
    "right-shift",  # 13
    "jump-back",  # 14
    "jump-forward",  # 15
)

x86_REGISTERS = (
    "di",  # 0: rr
    "si",  # 1: r1
    "bx",  # 2: r2
    "bp",  # 3: r3
)


def to_register(reg_num):
    return "%" + x86_REGISTERS[reg_num]


def to_hex_imm(byte):
    return f"$0x{byte:0>2X}"


JUMP_COMPARISON_TYPES = ("jmp", "je", "jb", "jbe", None, "jne", "jae", "ja")

JUMP_LABEL_PREFIX = "b8_vm_label_"

x86_START = """\
.globl main
.section .rodata
format: .asciz "%02X"
.text
b8_vm_printf:
    push %si
    movzwl %di, %esi
    lea format, %edi
    xor %ax, %ax
    call printf@plt
    pop %si
    ret
main:
"""

x86_OUTPUT_PATH = "x86_assembly_output.s"

x86_EXECUTABLE_PATH = "x86_executable"
