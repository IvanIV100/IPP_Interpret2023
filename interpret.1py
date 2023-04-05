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
labels = None
label_jump = None


current_instruction = 0
done_instruction_count = 0


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


class Variable:
    def __init__(self, name, value, type_var):
        self.name = name
        self.value = value
        self.type_var = type_var

    def change_var(self, value, type_var):
        self.value = value
        self.type_var = type_var


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
    return xml_list


# check if using correctly
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


def handle_variable(var_to_handle, data=None):
    global GF
    global TF
    global LF

    frame = var_to_handle.split("@")[0]
    var_name = var_to_handle.split("@")[1]

    match frame:
        case "GF":
            if var_name not in GF:
                Error.error_exit(variableNotDefined)
            if data:
                var_built = Variable(var_name, data.value, data.type)
                GF[var_name] = var_built
                return GF[var_name]
            else:
                return GF[var_name]
        case "TF":
            if TF == None:
                Error.error_exit(frameNotExists)
            elif var_name not in TF:
                Error.error_exit(variableNotDefined)
            else:
                if data:
                    var_built = Variable(var_name, data.value, data.type)
                    TF[var_name] = var_built
                    return TF[var_name]
                else:
                    return TF[var_name]
        case "LF":
            if len(LF) == 0:
                Error.error_exit(frameNotExists)
            if var_name not in LF[-1]:
                Error.error_exit(variableNotDefined)
            if data:
                var_built = Variable(var_name, data.value, data.type)
                LF[-1][var_name] = var_built
                return LF[-1][var_name]
            else:
                return LF[-1][var_name]
        case _:
            Error.error_exit(wrongOperandType)


def no_argument_instruction(instruction):
    global TF
    global LF
    global GF
    global current_instruction
    global stack_return
    match instruction.name.upper():
        case "CREATEFRAME":
            TF = {}

        case "PUSHFRAME":
            if TF == None:
                Error.error_exit(frameNotExists)
            LF.append(TF)
            TF = None

        case "POPFRAME":
            if len(LF) == 0:
                Error.error_exit(frameNotExists)
            TF = LF.pop()

        case "RETURN":
            if len(stack_return) == 0:
                Error.error_exit(missingValue)
            current_instruction = stack_return.pop()

        case "BREAK":
            # add more info
            sys.stderr.write("Current instruction count: " + str(current_instruction) + "\n")


def one_argument_instruction(instruction, labels=None):
    global stack_push
    global data_to_transfer
    global source_first
    global current_instruction

    match instruction.name.upper():

        case "PUSHS":
            source_first = instruction.arguments[0].name
            data_to_transfer = handle_variable(source_first)
            stack_push.append(data_to_transfer)

        case "POPS":
            if len(stack_push) == 0:
                Error.error_exit(missingValue)
            data_to_transfer = stack_push.pop()
            handle_variable(instruction.arguments[0].name, data_to_transfer)

        case "DEFVAR":
            split_tuple = instruction.arguments[0].name.split("@")
            frame = split_tuple[0]
            var_name = split_tuple[1]
            # check scopes and names reference
            if var_name in GF or var_name in TF or var_name in LF[-1]:
                Error.error_exit(semantics)
            match frame:
                case "GF":
                    GF[var_name] = None
                case "TF":
                    TF[var_name] = None
                case "LF":
                    LF[-1][var_name] = None

        case "CALL":
            stack_return.append(current_instruction+1)
            current_instruction = labels[instruction.arguments[0].name]

        case "LABEL":
            pass    # already handled

        case "JUMP":
            current_instruction = labels[instruction.arguments[0].name]

        case "DPRINT":
            if instruction.arguments[0].type == "var":
                data_to_transfer = handle_variable(instruction.arguments[0].name)
                sys.stderr.write(str(data_to_transfer.value) + "\n")
            else:
                # check if instruction passed is in somethign@something format
                data_to_transfer = instruction.arguments[0].name
                sys.stderr.write(str(data_to_transfer) + "\n")
        case "WRITE":
            if instruction.arguments[0].type == "var":
                data_to_transfer = handle_variable(instruction.arguments[0].name)
            else:
                data_to_transfer = instruction.arguments[0].name
            sys.stdout.write(str(data_to_transfer) + "\n")
        case "EXIT":
            if int(instruction.arguments[0].name) < 0 or int(instruction.arguments[0].name) > 49:
                Error.error_exit(wrongOperandValue)
            exit(int(instruction.arguments[0].name))


def two_argument_instruction(instruction):
    global data_to_transfer
    global source_first
    global source_second
    match instruction.name.upper():
        case "MOVE":
            if instruction.arguments[1].type == "var":
                data_to_transfer = handle_variable(instruction.arguments[1].name)
            else:
                data_to_transfer = instruction.arguments[1].name
            handle_variable(instruction.arguments[0].name, data_to_transfer)

        case "INT2CHAR":
            try:
                data_to_transfer = chr(instruction.arguments[1].name)
            except ValueError:
                Error.error_exit(wrongStringManipulation)
            handle_variable(instruction.arguments[0].name, data_to_transfer)

        case "STRLEN":
            data_to_transfer = len(instruction.arguments[1].name)
            handle_variable(instruction.arguments[0].name, data_to_transfer)

        case "TYPE":
            data_to_transfer = instruction.arguments[1].type
            handle_variable(instruction.arguments[0].name, data_to_transfer)

        case "NOT":
            # finish this
            print("NOT")


def three_argument_instruction(instruction):
    global data_to_transfer
    global current_instruction
    global labels
    global label_jump

    match instruction.name.upper():
        case "ADD":
            if instruction.arguments[1].type == "int" and instruction.arguments[2].type == "int":
                data_to_transfer = int(instruction.arguments[1].name) + int(instruction.arguments[2].name)
            else:
                Error.error_exit(wrongOperandType)
            res_var = Variable(data_to_transfer, "int")
            handle_variable(instruction.arguments[0].name, res_var)

        case "SUB":
            if instruction.arguments[1].type == "int" and instruction.arguments[2].type == "int":
                data_to_transfer = int(instruction.arguments[1].name) - int(instruction.arguments[2].name)
            else:
                Error.error_exit(wrongOperandType)
            res_var = Variable(data_to_transfer, "int")
            handle_variable(instruction.arguments[0].name, res_var)

        case "MUL":
            if instruction.arguments[1].type == "int" and instruction.arguments[2].type == "int":
                data_to_transfer = int(instruction.arguments[1].name) * int(instruction.arguments[2].name)
            else:
                Error.error_exit(wrongOperandType)

            res_var = Variable(data_to_transfer, "int")
            handle_variable(instruction.arguments[0].name, res_var)

        case "IDIV":
            if int(instruction.arguments[2].name) == 0:
                Error.error_exit(wrongOperandValue)
            if instruction.arguments[1].type == "int" and instruction.arguments[2].type == "int":
                data_to_transfer = int(instruction.arguments[1].name) / int(instruction.arguments[2].name)
            else:
                Error.error_exit(wrongOperandType)

            res_var = Variable(data_to_transfer, "int")
            handle_variable(instruction.arguments[0].name, res_var)

        case "LT":
            # check if both argument1 and argument2 are same type and if they are compare them < and return bool value write it to argument0
            if instruction.arguments[1].type == instruction.arguments[2].type:
                if instruction.arguments[1].type == "int":
                        if int(instruction.arguments[1].name) < int(instruction.arguments[2].name):
                            data_to_transfer = Variable(True, "bool")
                        else:
                            data_to_transfer = Variable(False, "bool")
                elif instruction.arguments[1].type == "string":
                    if instruction.arguments[1].name < instruction.arguments[2].name:
                        data_to_transfer = Variable(True, "bool")
                    else:
                        data_to_transfer = Variable(False, "bool")
                elif instruction.arguments[1].type == "bool":
                    if instruction.arguments[1].name < instruction.arguments[2].name:
                        data_to_transfer = Variable(True, "bool")
                    else:
                        data_to_transfer = Variable(False, "bool")
            handle_variable(instruction.arguments[0].name, data_to_transfer)

        case "GT":
            # check if both argument1 and argument2 are same type and if they are compare them > and return bool value write it to argument0
            if instruction.arguments[1].type == instruction.arguments[2].type:
                if instruction.arguments[1].type == "int":
                        if int(instruction.arguments[1].name) > int(instruction.arguments[2].name):
                            data_to_transfer = Variable(True, "bool")
                        else:
                            data_to_transfer = Variable(False, "bool")
                elif instruction.arguments[1].type == "string":
                    if instruction.arguments[1].name > instruction.arguments[2].name:
                        data_to_transfer = Variable(True, "bool")
                    else:
                        data_to_transfer = Variable(False, "bool")
                elif instruction.arguments[1].type == "bool":
                    if instruction.arguments[1].name > instruction.arguments[2].name:
                        data_to_transfer = Variable(True, "bool")
                    else:
                        data_to_transfer = Variable(False, "bool")
            handle_variable(instruction.arguments[0].name, data_to_transfer)

        case "EQ":
            # check if both argument1 and argument2 are same type and if they are compare them == and return bool value write it to argument0
            if instruction.arguments[1].type == instruction.arguments[2].type:
                if instruction.arguments[1].type == "int":
                    if int(instruction.arguments[1].name) == int(instruction.arguments[2].name):
                        data_to_transfer = Variable(True, "bool")
                    else:
                        data_to_transfer = Variable(False, "bool")
                elif instruction.arguments[1].type == "string":
                    if instruction.arguments[1].name == instruction.arguments[2].name:
                        data_to_transfer = Variable(True, "bool")
                    else:
                        data_to_transfer = Variable(False, "bool")
                elif instruction.arguments[1].type == "bool":
                    if instruction.arguments[1].name == instruction.arguments[2].name:
                        data_to_transfer = Variable(True, "bool")
                    else:
                        data_to_transfer = Variable(False, "bool")
            handle_variable(instruction.arguments[0].name, data_to_transfer)

        case "AND":
            # check if argument1 and argument2 are bool and if they are compare them and return bool value write it to argument0
            if instruction.arguments[1].type == "bool" and instruction.arguments[2].type == "bool":
                if instruction.arguments[1].name == "true" and instruction.arguments[2].name == "true":
                    data_to_transfer = Variable(True, "bool")
                else:
                    data_to_transfer = Variable(False, "bool")
            handle_variable(instruction.arguments[0].name, data_to_transfer)

        case "OR":
            # check if argument1 and argument2 are bool and if they are OR them and return bool value write it to argument0
            if instruction.arguments[1].type == "bool" and instruction.arguments[2].type == "bool":
                if instruction.arguments[1].name == "true" or instruction.arguments[2].name == "true":
                    data_to_transfer = Variable(True, "bool")
                else:
                    data_to_transfer = Variable(False, "bool")
            handle_variable(instruction.arguments[0].name, data_to_transfer)

        case "STRI2INT":
            # check if argument1 is string and argument 2 is int and if they are convert char at position argument2 to int and write it to argument0
            if instruction.arguments[1].type == "string" and instruction.arguments[2].type == "int":
                if int(instruction.arguments[2].name) < len(instruction.arguments[1].name):
                    data_to_transfer = ord(instruction.arguments[1].name[int(instruction.arguments[2].name)])
                else:
                    Error.error_exit(wrongOperandValue)
            else:
                Error.error_exit(wrongOperandType)
            handle_variable(instruction.arguments[0].name, data_to_transfer)

        case "CONCAT":
            # check if argument1 and argument2 are string and if they are concatenate them and write it to argument0
            if instruction.arguments[1].type == "string" and instruction.arguments[2].type == "string":
                data_to_transfer = instruction.arguments[1].name + instruction.arguments[2].name
            else:
                Error.error_exit(wrongOperandValue)
            handle_variable(instruction.arguments[0].name, data_to_transfer)

        case "GETCHAR":
            # check if argument1 is string and argument 2 is int and if they are get char at position argument2 and write it to argument0
            if instruction.arguments[1].type == "string" and instruction.arguments[2].type == "int":
                if int(instruction.arguments[2].name) < len(instruction.arguments[1].name):
                    data_to_transfer = instruction.arguments[1].name[int(instruction.arguments[2].name)]
                else:
                    Error.error_exit(wrongOperandValue)
            else:
                Error.error_exit(wrongOperandType)
            handle_variable(instruction.arguments[0].name, data_to_transfer)

        case "SETCHAR":
            # check if argument2 is string and argument 1 is int. check if Var from argument 0 is not empty.set first char from argument2 to position argument1 in argument0
            if instruction.arguments[1].type == "string" and instruction.arguments[2].type == "int":
                #fix handle variable
                if int(instruction.arguments[2].name) < len(instruction.arguments[0].name):
                    char_to_insert = instruction.arguments[2].name[0]
                    num = int(instruction.arguments[1].name)
                    var_to_change = handle_variable(instruction.arguments[0].name, None)
                    var_to_change.name = var_to_change.name[:num] + char_to_insert + var_to_change.name[num + 1:]
                    handle_variable(instruction.arguments[0].name, var_to_change)
                else:
                    Error.error_exit(wrongOperandValue)
            else:
                Error.error_exit(wrongOperandType)
        case "JUMPIFEQ":
            # check if argument1 and argument2 are same type and if they are compare them == and if they are equal jump to label
            if instruction.arguments[1].type == instruction.arguments[2].type:
                if instruction.arguments[1].type == "int":
                    if int(instruction.arguments[1].name) == int(instruction.arguments[2].name):
                        label_jump = instruction.arguments[0].name
                        current_instruction = labels[label_jump]
                elif instruction.arguments[1].type == "bool":
                    if instruction.arguments[1].name == instruction.arguments[2].name:
                        label_jump = instruction.arguments[0].name
                        current_instruction = labels[label_jump]
                elif instruction.arguments[1].type == "string":
                    if instruction.arguments[1].name == instruction.arguments[2].name:
                        label_jump = instruction.arguments[0].name
                        current_instruction = labels[label_jump]


        case "JUMPIFNEQ":
            # check if argument1 and argument2 are same type and if they are compare them != and if they are not equal jump to label
            if instruction.arguments[1].type == instruction.arguments[2].type:
                if instruction.arguments[1].type == "int":
                    if int(instruction.arguments[1].name) != int(instruction.arguments[2].name):
                        label_jump = instruction.arguments[0].name
                        current_instruction = labels[label_jump]
                elif instruction.arguments[1].type == "bool":
                    if instruction.arguments[1].name != instruction.arguments[2].name:
                        label_jump = instruction.arguments[0].name
                        current_instruction = labels[label_jump]
                elif instruction.arguments[1].type == "string":
                    if instruction.arguments[1].name != instruction.arguments[2].name:
                        label_jump = instruction.arguments[0].name
                        current_instruction = labels[label_jump]


def interpret_code(list_instruct, input_split):
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
    global done_instruction_count

    global labels
    labels= label_index(list)

    while current_instruction < len(list_instruct):
        instruction = list_instruct[current_instruction]
        current_instruction += 1
        done_instruction_count += 1

        for argument in instruction.arguments:
            if argument.name.upper() in ("CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK"):
                no_argument_instruction(argument)

            elif argument.name.upper() in ("PUSHS", "POPS", "DEFVAR", "CALL", "LABEL", "JUMP", "DPRINT", "WRITE", "EXIT"):
                one_argument_instruction(argument, labels)

            elif argument.name.upper() in ("MOVE", "INT2CHAR", "STRLEN", "TYPE"):
                two_argument_instruction(argument)

            elif argument.name.upper() in ("ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "NOT", "STRI2INT", "CONCAT", "GETCHAR", "SETCHAR", "JUMPIFEQ", "JUMPIFNEQ"):
                three_argument_instruction(argument)

            else:
                Error.error_exit(wrongOperandType)


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

    interpret_code(list_instructions, input_split)

    exit(0)


if __name__ == '__main__':
    main()

