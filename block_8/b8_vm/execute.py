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

class Translator:
    def __init__(self):
        state = {
            "instruction": None,
            "x86_command": None,
            "x86_args": [],
            "ri_indicator_1": None,
            "ri_indicator_2": None,
            "dest_register": None,
            "db_indicator": None,
            "la_indicator": None,
            "compare_first_arg": None,
            "compare_first_arg_pos": None,
            "byte_number": 0,
            "instr_byte_number": 1,
            "jump_label_byte_numbers": set(),
            # "jump_comparison_type": None
        }
        mode = INSTRUCTION_MODE
        x86_output = dict()

    def execute(self, byte):
        upper = (byte >> 4) & 0x0F
        lower = byte & 0x0F
        if self.mode == INSTRUCTION_MODE:
            self.state["instruction"] = INSTRUCTION_CODES[upper]
        # print(state["instruction"])

        if self.state["instruction"] == "push_pop":
            if not (lower & 0b100) or self.mode == ARGUMENT_MODE:
                self.push(byte, upper, lower)
            else:  # Pop
                self.pop(lower)
        elif self.state["instruction"] == "no_op_pause":
            self.no_op_pause(lower)
        elif self.state["instruction"] == "compare":
            self.compare(byte, upper, lower)
        elif self.state["instruction"] == "jump-back" or state["instruction"] == "jump-forward":
            self.jump(byte, upper, lower)
        else:
            if self.mode == INSTRUCTION_MODE:
                self.state["ri_indicator_1"] = bool(lower & 0b1000)
                self.state["dest_register"] = lower & 0b0011
                if self.state["instruction"] == "move":
                    self.state["x86_command"] = "mov"
                elif self.state["instruction"] == "add":
                    self.state["x86_command"] = "add"
                elif self.state["instruction"] == "subtract":
                    self.state["x86_command"] = "sub"
                elif self.state["instruction"] == "multiply":
                    self.state["x86_command"] = "mul"
                elif self.state["instruction"] == "divide":
                    self.state["x86_command"] = "div"
                elif self.state["instruction"] == "bit-and":
                    self.state["x86_command"] = "and"
                elif self.state["instruction"] == "bit-or":
                    self.state["x86_command"] = "or"
                elif self.state["instruction"] == "bit-xor":
                    self.state["x86_command"] = "xor"
                elif self.state["instruction"] == "left-shift":
                    self.state["x86_command"] = "sal"
                mode = ARGUMENT_MODE
            else:
                self.state["x86_args"] = [to_register(self.state["dest_register"])]
                if not self.state["ri_indicator_1"]:
                    self.state["x86_args"].insert(0, to_register(lower & 0b0011))
                else:
                    self.state["x86_args"].insert(0, to_hex_imm(byte))
                mode = INSTRUCTION_MODE


    def pop(self, lower):
        assert not (lower & 0b1000)
        dest = lower & 0b0011
        self.state["x86_command"] = "pop"
        self.state["x86_args"] = [to_register(dest)]


    def push(self, byte, upper, lower):
        if self.mode == INSTRUCTION_MODE:
            if not (lower & 0b1000):
                # state["x86_command"] = "push"
                # state["x86_args"] = [to_register(lower & 0b11)]
                self.state["x86_command"] = "call"
                self.state["x86_args"] = [f"push_{to_register(lower & 0b11)}"]
            else:
                self.mode = ARGUMENT_MODE
        else:
            self.state["x86_command"] = "push"
            self.state["x86_args"] = ["$" + byte]


    def no_op_pause(self, lower):
        if lower & 0b0001:
            self.state["x86_command"] = "call"
            self.state["x86_args"] = ["b8_vm_printf"]
        else:
            self.state["x86_command"] = "nop"
            self.state["x86_args"] = []


    def compare(self, byte, upper, lower):
        if self.mode == INSTRUCTION_MODE:
            self.state["ri_indicator_1"] = bool(lower & 0b1000)
            self.state["ri_indicator_2"] = bool(lower & 0b0100)
            self.state["db_indicator"] = bool(lower & 0b0001)
            self.mode = ARGUMENT_MODE
        else:
            if not (self.state["ri_indicator_1"] or self.state["ri_indicator_2"]):
                cmp_register_1 = lower >> 2
                cmp_register_2 = lower & 0b0011
                self.state["x86_command"] = "test" if self.state["db_indicator"] else "cmp"
                self.state["x86_args"] = [
                    to_register(cmp_register_2),
                    to_register(cmp_register_1),
                ]
                self.mode = INSTRUCTION_MODE
            elif self.state["instr_byte_number"] == 2:
                if self.state["ri_indicator_1"] and not self.state["ri_indicator_2"]:
                    self.state["compare_first_arg"] = to_register(lower & 0b0011)
                    self.state["compare_first_arg_pos"] = 1
                elif self.state["ri_indicator_2"] and not self.state["ri_indicator_1"]:
                    self.state["compare_first_arg"] = to_register(lower & 0b0011)
                    self.state["compare_first_arg_pos"] = 0
                else:
                    self.state["compare_first_arg"] = to_hex_imm(byte)
                    self.state["compare_first_arg_pos"] = 0
            elif self.state["instr_byte_number"] == 3:
                self.state["x86_command"] = "test" if self.state["db_indicator"] else "cmp"
                self.state["x86_args"] = [to_hex_imm(byte)]
                self.state["x86_args"].insert(
                    self.state["compare_first_arg_pos"], self.state["compare_first_arg"]
                )
                self.state["x86_args"] = reversed(self.state["x86_args"])
                self.mode = INSTRUCTION_MODE


    def jump(self, byte, upper, lower):
        if self.mode == INSTRUCTION_MODE:
            self.state["ri_indicator_1"] = bool(lower & 0b1000)
            self.state["x86_command"] = JUMP_COMPARISON_TYPES[lower & 0b0111]
            assert self.state["x86_command"]
            self.mode = ARGUMENT_MODE
        else:
            if not self.state["ri_indicator_1"]:
                self.state["x86_args"] = [to_register(lower & 0b0011)]
            else:
                jump_pos = self.state["byte_number"] + (byte if self.state["instruction"] == "jump-forward" else -byte)
                self.state["jump_label_byte_numbers"].add(jump_pos)
                self.state["x86_args"] = [JUMP_LABEL_PREFIX + str(jump_pos)]
            self.mode = INSTRUCTION_MODE
