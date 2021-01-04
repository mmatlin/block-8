import sys
from .consts import (
    INSTRUCTION_MODE,
    ARGUMENT_MODE,
    INSTRUCTION_CODES,
    to_register,
    to_hex_imm,
    JUMP_COMPARISON_TYPES,
    JUMP_LABEL_PREFIX,
)


def execute(byte, state, mode):
    upper = (byte >> 4) & 0x0F
    lower = byte & 0x0F
    if mode == INSTRUCTION_MODE:
        state["instruction"] = INSTRUCTION_CODES[upper]
    # print(state["instruction"])

    if state["instruction"] == "push_pop":
        if not (lower & 0b100) or mode == ARGUMENT_MODE:
            state, mode = push(byte, upper, lower, state, mode)
        else:  # Pop
            state = pop(lower, state)
    elif state["instruction"] == "no_op_pause":
        state = no_op_pause(lower, state)
    elif state["instruction"] == "compare":
        state, mode = compare(byte, upper, lower, state, mode)
    elif state["instruction"] == "jump-back" or state["instruction"] == "jump-forward":
        state, mode = jump(byte, upper, lower, state, mode)
    else:
        if mode == INSTRUCTION_MODE:
            state["ri_indicator_1"] = bool(lower & 0b1000)
            state["dest_register"] = lower & 0b0011
            if state["instruction"] == "move":
                state["x86_command"] = "mov"
            elif state["instruction"] == "add":
                state["x86_command"] = "add"
            elif state["instruction"] == "subtract":
                state["x86_command"] = "sub"
            elif state["instruction"] == "multiply":
                state["x86_command"] = "mul"
            elif state["instruction"] == "divide":
                state["x86_command"] = "div"
            elif state["instruction"] == "bit-and":
                state["x86_command"] = "and"
            elif state["instruction"] == "bit-or":
                state["x86_command"] = "or"
            elif state["instruction"] == "bit-xor":
                state["x86_command"] = "xor"
            elif state["instruction"] == "left-shift":
                state["x86_command"] = "sal"
            mode = ARGUMENT_MODE
        else:
            state["x86_args"] = [to_register(state["dest_register"])]
            if not state["ri_indicator_1"]:
                state["x86_args"].insert(0, to_register(lower & 0b0011))
            else:
                state["x86_args"].insert(0, to_hex_imm(byte))
            mode = INSTRUCTION_MODE

    return state, mode


def pop(lower, state):
    assert not (lower & 0b1000)
    dest = lower & 0b0011
    state["x86_command"] = "pop"
    state["x86_args"] = [to_register(dest)]
    return state


def push(byte, upper, lower, state, mode):
    if mode == INSTRUCTION_MODE:
        if not (lower & 0b1000):
            # state["x86_command"] = "push"
            # state["x86_args"] = [to_register(lower & 0b11)]
            state["x86_command"] = "call"
            state["x86_args"] = [f"push_{to_register(lower & 0b11)}"]
        else:
            mode = ARGUMENT_MODE
    else:
        state["x86_command"] = "push"
        state["x86_args"] = ["$" + byte]
    return state, mode


def no_op_pause(lower, state):
    if lower & 0b0001:
        state["x86_command"] = "call"
        state["x86_args"] = ["b8_vm_printf"]
    else:
        state["x86_command"] = "nop"
        state["x86_args"] = []
    return state


def compare(byte, upper, lower, state, mode):
    if mode == INSTRUCTION_MODE:
        state["ri_indicator_1"] = bool(lower & 0b1000)
        state["ri_indicator_2"] = bool(lower & 0b0100)
        state["db_indicator"] = bool(lower & 0b0001)
        mode = ARGUMENT_MODE
    else:
        if not (state["ri_indicator_1"] or state["ri_indicator_2"]):
            cmp_register_1 = lower >> 2
            cmp_register_2 = lower & 0b0011
            state["x86_command"] = "test" if state["db_indicator"] else "cmp"
            state["x86_args"] = [
                to_register(cmp_register_2),
                to_register(cmp_register_1),
            ]
            mode = INSTRUCTION_MODE
        elif state["instr_byte_number"] == 2:
            if state["ri_indicator_1"] and not state["ri_indicator_2"]:
                state["compare_first_arg"] = to_register(lower & 0b0011)
                state["compare_first_arg_pos"] = 1
            elif state["ri_indicator_2"] and not state["ri_indicator_1"]:
                state["compare_first_arg"] = to_register(lower & 0b0011)
                state["compare_first_arg_pos"] = 0
            else:
                state["compare_first_arg"] = to_hex_imm(byte)
                state["compare_first_arg_pos"] = 0
        elif state["instr_byte_number"] == 3:
            state["x86_command"] = "test" if state["db_indicator"] else "cmp"
            state["x86_args"] = [to_hex_imm(byte)]
            state["x86_args"].insert(
                state["compare_first_arg_pos"], state["compare_first_arg"]
            )
            state["x86_args"] = reversed(state["x86_args"])
            mode = INSTRUCTION_MODE
    return state, mode


def jump(byte, upper, lower, state, mode):
    if mode == INSTRUCTION_MODE:
        state["ri_indicator_1"] = bool(lower & 0b1000)
        state["x86_command"] = JUMP_COMPARISON_TYPES[lower & 0b0111]
        assert state["x86_command"]
        mode = ARGUMENT_MODE
    else:
        if not state["ri_indicator_1"]:
            state["x86_args"] = [to_register(lower & 0b0011)]
        else:
            jump_pos = state["byte_number"] + (byte if state["instruction"] == "jump-forward" else -byte)
            state["jump_label_byte_numbers"].add(jump_pos)
            state["x86_args"] = [JUMP_LABEL_PREFIX + str(jump_pos)]
        mode = INSTRUCTION_MODE
    return state, mode
