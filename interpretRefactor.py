#!/usr/bin/env python3
import readline
import sys
import argparse
import xml.etree.ElementTree as ET
import re

# Global variables
global_frame = {}
local_frame = {}
temp_frame = None

data_stack = {}
call_stack = {}
labels_ordered = {}

current_instruction_index = 0
done_instructions = 0


class Argument:
    def __init__(self, val_type, value="", order=0):
        self.val_type = val_type
        self.value = value
        self.order = int(order)

    # maybe fix
    def __eq__(self, other):
        return self.val_type == other.val_type

    def __not_eq__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "Type: " + self.val_type + " Value: " + self.value + " Order: " + str(self.order)


class Instruction:
    def __init__(self, opcode, arg_list, order=None):
        self.opcode = opcode.upper()
        self.arg_list = arg_list
        if order:
            self.order = int(order)
        else:
            self.order = None

    def __str__(self):
        return "Opcode: " + self.opcode + " Arguments: " + str(self.arg_list)

    def __eq__(self, other):
        return self.opcode == other.opcode and self.arg_list == other.arg_list

    def __not_eq__(self, other):
        return not self.__eq__(other)


class Variable:
    def __init__(self, name, value, var_type):
        self.name = name
        self.value = value
        self.var_type = var_type

    def __str__(self):
        return "Name: " + self.name + " Value: " + self.value + " Type: " + self.var_type

    def __update_value(self, value, var_type):
        self.value = value
        self.var_type = var_type

class Error:

    def __init__(self, description, code):
        self.description = description
        self.code = code

    def __str__(self):
        return self.description

    def error_exit(self):
        sys.stderr.write(self.description)
        sys.exit(self.code)


wrongParameters = Error("Missing parameter or illegal combination\n", 10)
cannotOpenSourceFiles = Error("Cannot open source files\n", 11)
cannotOpenOutputFiles = Error("Cannot open files to write\n", 12)
internalError = Error("Internal error\n", 99)
xmlNotWellFormated = Error("Wrong XML syntax, not well formatted\n", 31)
xmlStructureSyntaxLex = Error("Wrong XML structure or syntactic/lexical error\n", 32)
semantics = Error("semantics error in XML, e.g. not defined label or redefinition of label\n", 52)
wrongOperandType = Error("Wrong operand type\n", 53)
variableNotDefined = Error("Accessing not defined variable, frame exists\n", 54)
frameNotExists = Error("Frame not exists\n", 55)
missingValue = Error("Missing value in variable or stack\n", 56)
wrongOperandValue = Error("Wrong operand value, e.g. division by zero\n", 57)
wrongStringManipulation = Error("Wrong string manipulation", 58)



def argument_parser():
    parser = argparse.ArgumentParser(description='Basic XML to IPPCode23 interpret')
    parser.add_argumen('--source', nargds='?', help='Source File')
    parser.add_argument('--inout', nargs='?', help='Input File')
    arguments = parser.parse_args()

    control_list=[]
    if arguments.source:
        control_list.append(arguments.source)
    if arguments.input:
        control_list.append(arguments.input)
    if len(control_list) == 0:
        Error.error_exit(wrongParameters)

    return arguments.source, arguments.input


def split_to_lines(file):
    if file:
        try:
            with open (file, "r") as in_file:
                data_lines = in_file.readlines()
                in_file.close()
        except (Exception,):
            Error.error_exit(cannotOpenSourceFiles)
    else:
        return None
    return [line.strip for line in data_lines]


def load_xml_to_list(root):
    list = []

    for child in root:
        child_arguments = []

        # maybe missing check xml arg order correct
        for each in child:
            output = re.search("^arg([1-3])$", each.tag)
            output_ord = output.group(1)
            argument = Argument(each.attrib["type"], each.text, output_ord)
            child_arguments.append(argument)

        child_arguments.sort(key=lambda argument: argument.order)

        for index, argument in enumerate(child_arguments, start=1):
            if argument.order != index:
                Error.error_exit(xmlStructureSyntaxLex)
        # maybe fix child.get
        instruction = Instruction(child.attrib["opcode"], child_arguments, child.attrib["order"])
        list.append(instruction)
    list.sort(key=lambda instruction: instruction.order)
    return list

        # if child.tag != "instruction":
        #     Error.error_exit(xmlStructureSyntaxLex)
        # instruction = Instruction(child.attrib["opcode"], [])
        # for arg in child:
        #     if arg.tag != "arg1" and arg.tag != "arg2" and arg.tag != "arg3":
        #         Error.error_exit(xmlStructureSyntaxLex)
        #     if arg.attrib["type"] != "var" and arg.attrib["type"] != "label" and arg.attrib["type"] != "type" and arg.attrib["type"] != "symb":
        #         Error.error_exit(xmlStructureSyntaxLex)
        #     if arg.attrib["type"] == "var":
        #         if not re.match(r"^(GF|LF|TF)@([a-zA-Z]|_|-|\$|&|%|\*|!|\?)([a-zA-Z]|_|-|\$|&|%|\*|!|\?|[0-9])*", arg.text):
        #             Error.error_exit(xmlStructureSyntaxLex)
        #     if arg.attrib["type"] == "label":
        #         if not re.match(r"^([a-zA-Z]|_|-|\$|&|%|\*|!|\?)([a-zA-Z]|_|-|\$|&|%|\*|!|\?|[0-9])*", arg.text):
        #             Error.error_exit(xmlStructureSyntaxLex)
        #     if arg.attrib["type"] == "type":
        #         if arg.text != "int" and arg.text != "string" and arg.text != "bool":
        #             Error.error_exit(xmlStructureSyntaxLex)
        #     if arg.attrib["type"] == "symb":
        #         if arg.text != "int" and arg.text != "string" and arg.text != "bool" and arg.text != "nil" and arg.text != "label" and arg.text != "type" and arg.text != "var":
        #             Error.error_exit(xmlStructureSyntaxLex)
        #     argument = Argument(arg.attrib["type"], arg.text, arg.attrib["order"])
        #     instruction.arg_list.append(argument)
        # list.append(instruction)


def main():
    source_file = None
    input_file = None
    source_file, input_file = argument_parser()

    if source_file:
        source_file_split = split_to_lines(source_file)
    else:
        # check if reading is correct
        source_file_split = [line.strip for line in sys.stdin]
    exit()

    if input_file:
        input_file_split = split_to_lines(input_file)
    else:
        input_file_split = [line.strip for line in sys.stdin]

    try:
        root = ET.fromstring(source_file_split)
    except(Exception,):
        Error.error_exit(xmlNotWellFormated)

    instruction_list = load_xml_to_list(root)


if __name__ == '__main__':
    main()
