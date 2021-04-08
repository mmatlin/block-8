import sys
import argparse
from pathlib import Path
import subprocess
from .execute import Translator, execute
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
    # block_8 sbt program1
    # program1 (bytes):
    #     00011001 00101011
    #
    # block_8 sbt -mb "0001 1001 0010 1011"
    #
    # block_8 sbt -m "0001 1001 0010 1011"
    #
    # block_8 sbt -mh "15 2B"
    translator = Translator()
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
            translator.execute(byte)
            translator.state["instr_byte_number"] += 1
            if translator.mode == INSTRUCTION_MODE:
                # if byte_number in label_poses:
                # x86_output.append(f"b8_vm_label_{state['jump_number']}:")
                # state["jump_number"] += 1
                translator.x86_output[translator.state["byte_number"]] = {
                    "x86_instruction": f"{translator.state['x86_command']} "
                    + ", ".join(translator.state["x86_args"]),
                    "jump_label": None,
                }
                translator.state["instr_byte_number"] = 1
            translator.state["byte_number"] += 1
        for jump_label_byte_number in translator.state["jump_label_byte_numbers"]:
            translator.x86_output[jump_label_byte_number]["jump_label"] = jump_label_byte_number
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
                    for x86_instruction in translator.x86_output.values()
                ]
            )
            + "\nret\n"
        )
        x86_output_path = Path(x86_OUTPUT_PATH)
        x86_output_path.touch()
        with open(x86_output_path, "w") as x86_output_file:
            x86_output_file.write(output)
        subprocess.run(["gcc", x86_OUTPUT_PATH, "-o", x86_EXECUTABLE_PATH])


def run_from_entry_point():
    # parser = argparse.ArgumentParser(description="Run a Block-8 executable on an x86(-64) machine.")
    # parser.add_argument("-m", "--machine", action="store_const", const="b")
    # args = parser.parse_args()
    # print(args)
    print("hello!")
    # run("first_program", "filenam