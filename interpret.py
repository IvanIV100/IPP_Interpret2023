#!/usr/bin/env python3

import sys
import argparse
import xml.etree.ElementTree as ET
import re

GF = {}
LF = []
TF = None
stack_push = []
stack_return = []
data_to_transfer = None
data_in_place = None
source_first = None
source_second = None
label_jump = None

current_instruction = 0
done_count = 0


class Argument:
    def __init__(self, argtype, name="",  order=0):
        self.name = name
        self.type = argtype
        self.order = int(order)

    def __str__(self):
        if self.name:
            return self.name
        else:
            if self.argtype:
                return f" <{self.argtype}>"
            else:
                return ""

    def __eq__(self, other):

        if self.argtype == other.type:
            return True
        elif "symb" == self.argtype:
            if other.argtype in ("var", "string", "int", "bool", "nil"):
                return True
        elif "symb" == other.type:
            if self.argtype in ("var", "string", "int", "bool", "nil"):
                return True
        elif "type" == self.argtype:
            if other.argtype in ("string", "int", "bool"):
                return True
        elif "type" == other.argtype:
            if self.argtype in ("string", "int", "bool"):
                return True
        return False

    def __noteq__(self, other):
        return not __eq__(self, other)


class Instruction:
    def __init__(self, name, arguments, order=None):
        self.name = name.upper()
        self.arguments = arguments
        if order:
            self.order = int(order)
        else:
            self.order = None

    def __str__(self):

        result = str(self.name)

        for argument in self.arguments:
            result += " " + argument.__str__()

        if self.order:
            return result + " (" + str(self.order) + ")"
        else:
            return result

    def __eq__(self, other):
        return self.name == other.name and self.arguments == other.arguments

    def __ne__(self, other):
        return not self.__eq__(self, other)


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


def load_by_line(file):
    if file:
        try:
            with open(file, "r") as f:
                data = f.readlines()
                f.close()
        except (Exception,):
            Error.error_exit(cannotOpenSourceFiles)
    else:
        return None

    return [line.strip() for line in data]


def load_xml():
    tree = ET.parse('XMLSource.xml')



def parse_arguments():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--source', nargs='?', help='First argument')
    parser.add_argument('--input', nargs='?', help='Second argument')
    args = parser.parse_args()

    arg_list = []
    if args.source:
        arg_list.append(args.source)
    if args.input:
        arg_list.append(args.input)
    if len(arg_list) == 0:
        Error.error_exit(wrongParameters)
    return args.source, args.input


def format_xml_to_list(root):
    xml_list = []

    for child in root:
        child_arguments = []

        for argument_iter in child:
            output = re.search("^arg([1-3])$", argument_iter.tag)
            order = output.group(1)
            argument = Argument(argument_iter.get("type"), argument_iter.text, order)
            child_arguments.append(argument)

        child_arguments.sort(key=lambda argument: argument.order)

        for index, argument in enumerate(child_arguments, start=1):
            if argument.order != index:
                Error.error_exit(xmlStructureSyntaxLex)

        instruction = Instruction(child.get("opcode"), child_arguments, child.get("order"))
        xml_list.append(instruction)

    xml_list.sort(key=lambda instruction: instruction.order)
    # maybe add arg checks here.
    return xml_list


def check_labels(list_to_check):
    labels = []

    for instruction in list_to_check:
        if instruction.name == "LABEL":
            label_name = instruction.arguments[0].name
            if label_name in labels:
                Error.error_exit(semantics)

            labels.append(label_name)
        elif instruction.name != "LABEL":
            for argument in instruction.arguments:
                if argument.type == "label":
                    if argument.name not in labels:
                        Error.error_exit(semantics)


def label_index(list_cleared):
    labels_indexed = {}
    for index, instruction in enumerate(list_cleared):
        if instruction.name == "LABEL":
            label = instruction.arguments[0].name
            labels_indexed[label] = index
    return labels_indexed


def no_argument_instruction(instruction):
    match instruction.name.upper():
        case "CREATEFRAME":
            print("CREATEFRAME")
        case "PUSHFRAME":
            print("PUSHFRAME")
        case "POPFRAME":
            print("POPFRAME")
        case "RETURN":
            print("RETURN")
        case "BREAK":
            print("BREAK")

def one_argument_instruction(instruction):
    match instruction.name.upper():
        case "PUSHS":
            print("PUSHS")
        case "POPS":
            print("POPS")
        case "DEFVAR":
            print("DEFVAR")
        case "CALL":
            print("CALL")
        case "LABEL":
            print("LABEL")
        case "JUMP":
            print("JUMP")
        case "DPRINT":
            print("DPRINT")
        case "WRITE":
            print("WRITE")
        case "EXIT":
            print("EXIT")

def two_argument_instruction(instruction):
    match instruction.name.upper():
        case "MOVE":
            print("MOVE")
        case "INT2CHAR":
            print("INT2CHAR")
        case "STRLEN":
            print("STRLEN")
        case "TYPE":
            print("TYPE")


def three_argument_instruction(instruction):
    match instruction.name.upper():
        case "ADD":
            print("ADD")
        case "SUB":
            print("SUB")
        case "MUL":
            print("MUL")
        case "IDIV":
            print("IDIV")
        case "LT":
            print("LT")
        case "GT":
            print("GT")
        case "EQ":
            print("EQ")
        case "AND":
            print("AND")
        case "OR":
            print("OR")
        case "NOT":
            print("NOT")
        case "STRI2INT":
            print("STRI2INT")
        case "CONCAT":
            print("CONCAT")
        case "GETCHAR":
            print("GETCHAR")
        case "SETCHAR":
            print("SETCHAR")
        case "JUMPIFEQ":
            print("JUMPIFEQ")
        case "JUMPIFNEQ":
            print("JUMPIFNEQ")


def interpret_code(list_cleared, input_split):
    global GF
    global TF
    global LF
    global stack_push
    global stack_return
    global data_to_transfer
    global data_in_place
    global source_first
    global source_second
    global label_jump
    global current_instruction
    global done_count

    label_index(list_cleared)

    while current_instruction < len(list_cleared):
        instruction = list_cleared[current_instruction]
        current_instruction += 1
        done_count += 1

        for argument in instruction.arguments:
            if argument.name.upper() in ("CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK"):
                no_argument_instruction(argument)









def main():
    source_file, input_file = parse_arguments()
    if source_file:
        source_split = load_by_line(source_file)
    else:
        source_split = [line.strip() for line in sys.stdin]

    if input_file:
        input_split = load_by_line(input_file)
    else:
        input_split = [line.strip() for line in sys.stdin]

    try:
        root = ET.fromstringlist(source_split)
    except(Exception,):
        Error.error_exit(xmlNotWellFormated)

    list_instructions = format_xml_to_list(root)
    for each in list_instructions:
        print(each)
    check_labels(list_instructions)
    list_instructions_cleared = replace_escape_sequences(list_instructions)

    # interpret_code(list_instructions_cleared, input_split)

    exit(0)


if __name__ == '__main__':
    main()

