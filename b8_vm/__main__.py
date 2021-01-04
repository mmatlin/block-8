import sys
import argparse
from pathlib import Path
import subprocess
from .execute import execute
from .consts import (
    INSTRUCTION_MODE,
    ARGUMENT_MODE,
    JUMP_LABEL_PREFIX,
    x86_START,
    x86_OUTPUT_PATH,
    x86_EXECUTABLE_PATH,
)


def run(data, data_type):
    # Equivalent commands:
    # b8_vm program1
    # program1 (bytes):
    #     00011001 00101011
    #
    # b8_vm --mb "0001 1001 0010 1011"
    #
    # b8_vm --m "0001 1001 0010 1011"
    #
    # b8_vm --mh "15 2B"
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
    if data_type == "filename":
        binary = Path(data).read_bytes()
        # label_poses = []
        # label_pos = 0
        # while True:
        #     try:
        #         label_pos = binary.index(bytes.fromhex("E"), label_pos) + 1
        #         label_poses.append(label_pos + binary[label_pos])
        #     except ValueError:
        #         break
        # label_pos = 0
        # while True:
        #     try:
        #         label_pos = binary.index(bytes.fromhex("F"), label_pos) + 1
        #         label_poses.append(label_pos - binary[label_pos])
        #     except ValueError:
        #         break
        # state["jump_number"] = 1
        for byte in binary:
            state, mode = execute(byte, state, mode)
            state["instr_byte_number"] += 1
            if mode == INSTRUCTION_MODE:
                # if byte_number in label_poses:
                # x86_output.append(f"b8_vm_label_{state['jump_number']}:")
                # state["jump_number"] += 1
                x86_output[state["byte_number"]] = {
                    "x86_instruction": f"{state['x86_command']} "
                    + ", ".join(state["x86_args"]),
                    "jump_label": None,
                }
                state["instr_byte_number"] = 1
            state["byte_number"] += 1
        for jump_label_byte_number in state["jump_label_byte_numbers"]:
            x86_output[jump_label_byte_number]["jump_label"] = jump_label_byte_number
        # print(x86_output)
        output = x86_START
        output += (
            "\n".join(
                [
                    (
                        f"{JUMP_LABEL_PREFIX}{x86_instruction['jump_label']}:\n"
                        if x86_instruction["jump_label"]
                        else ""
                    )
                    + x86_instruction["x86_instruction"]
                    for x86_instruction in x86_output.values()
                ]
            )
            + "\nret\n"
        )
        x86_output_path = Path(x86_OUTPUT_PATH)
        x86_output_path.touch()
        with open(x86_output_path, "w") as x86_output_file:
            x86_output_file.write(output)
        subprocess.run(["gcc", x86_OUTPUT_PATH, "-o", x86_EXECUTABLE_PATH])


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Run a Block-8 executable on an x86(-64) machine.")
    # parser.add_argument("-m", "--machine", action="store_const", const="b")
    # args = parser.parse_args()
    # print(args)
    run("first_program", "filename")
