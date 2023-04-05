#!/usr/bin/env python3
import sys
import argparse
import xml.etree.ElementTree as ET
import re

# Global variables
global_frame = {}
local_frame = []
temp_frame = None

data_stack = []
call_stack = []
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
    def __init__(self, opcode, arg_list, order=0):
        if not opcode:
            Error.error_exit(internalError)
        self.opcode = opcode.upper()
        self.arg_list = arg_list
        if order:
            try:
                self.order = int(order)
            except (Exception,):
                Error.error_exit(internalError)
        else:
            self.order = None

    def __str__(self):
        return "Opcode: " + self.opcode + " Arguments: " + str(self.arg_list)

    def __eq__(self, other):
        return self.opcode == other.opcode and self.arg_list == other.arg_list

    def __not_eq__(self, other):
        return not self.__eq__(other)


class Variable:
    def __init__(self, name=None, value=None, var_type=None):
        self.name = name
        self.value = value
        self.var_type = var_type

    def __str__(self):
        return "Name: " + self.name + " Value: " + self.value + " Type: " + self.var_type

    def update_value(self, value, var_type):
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
semantics = Error("semantics error, e.g. not defined label or redefinition of label\n", 52)
wrongOperandType = Error("Wrong operand type\n", 53)
variableNotDefined = Error("Accessing not defined variable, frame exists\n", 54)
frameNotExists = Error("Frame not exists\n", 55)
missingValue = Error("Missing value in variable or stack\n", 56)
wrongOperandValue = Error("Wrong operand value, e.g. division by zero\n", 57)
wrongStringManipulation = Error("Wrong string manipulation", 58)


def argument_parser():
    parser = argparse.ArgumentParser(description='Basic XML to IPPCode23 interpret')
    parser.add_argument('--source', nargs='?', help='Source File')
    parser.add_argument('--input', nargs='?', help='Input File')
    arguments = parser.parse_args()

    control_list = []
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
            with open(file, "r") as in_file:
                data_lines = [line.strip() for line in in_file.readlines()]
                in_file.close()
        except (Exception,):
            Error.error_exit(cannotOpenSourceFiles)

    else:
        return None
    return data_lines


def load_xml_to_list(root):
    list_parsed = []

    for child in root:
        child_arguments = []

        # maybe missing check xml arg order correct
        for each in child:
            for att in each.attrib:
                if att != "type":
                    Error.error_exit(xmlStructureSyntaxLex)
            matched = re.search("^arg([1-3])$", each.tag)
            if not matched:
                Error.error_exit(xmlStructureSyntaxLex)

            order_num = matched.group(1)
            argument = Argument(each.get("type"), each.text, order_num)
            child_arguments.append(argument)
        child_arguments.sort(key=lambda argument: argument.order)

        for index, argument in enumerate(child_arguments, start=1):
            if argument.order != index:
                Error.error_exit(xmlStructureSyntaxLex)
        instruction = Instruction(child.get("opcode"), child_arguments, child.get("order"))
        list_parsed.append(instruction)
    list_parsed.sort(key=lambda instruction: instruction.order)
    return list_parsed


# check if type matches with value
def symbol_check_and_return(symbol):
    split = symbol.split("@")
    if len(split) != 2:
        Error.error_exit(xmlStructureSyntaxLex)

    type_symbol = split[0]
    val = split[1]
    output = Variable(None, val, type_symbol)
    return output


def variable_check_and_return(variable):
    global global_frame
    global local_frame
    global temp_frame

    frame = variable.split("@")[0]
    name = variable.split("@")[1]

    match frame:
        case "GF":
            if name not in global_frame:
                Error.error_exit(variableNotDefined)
            else:
                return global_frame[name]
        case "LF":
            if len(local_frame) == 0:
                Error.error_exit(frameNotExists)
            if name not in local_frame[-1]:
                Error.error_exit(variableNotDefined)
            else:
                return local_frame[-1][name]

        case "TF":
            if not temp_frame:
                Error.error_exit(frameNotExists)
            if name not in temp_frame:
                Error.error_exit(variableNotDefined)
            else:
                return temp_frame[name]


def execute_defvar(to_define):
    global global_frame
    global local_frame
    global temp_frame

    frame = to_define.split("@")[0]
    name = to_define.split("@")[1]

    match frame:
        case "GF":
            if name not in global_frame:
                global_frame[name] = Variable(name, None, None)
            else:
                Error.error_exit(semantics)

        case "LF":
            if len(local_frame) == 0:
                Error.error_exit(frameNotExists)
            if name not in local_frame[-1]:
                local_frame[-1][name] = Variable(name, None, None)
            else:
                Error.error_exit(semantics)

        case "TF":
            if not temp_frame:
                Error.error_exit(frameNotExists)
            if name not in temp_frame:
                temp_frame[name] = Variable(name, None, None)
            else:
                Error.error_exit(semantics)


def no_argument_instruction(instruction):
    global temp_frame
    global local_frame
    global call_stack
    global current_instruction_index
    global done_instructions

    match instruction.opcode.upper():
        case "CREATEFRAME":
            temp_frame = {}

        case "PUSHFRAME":
            if not temp_frame:
                Error.error_exit(frameNotExists)
            local_frame.append(temp_frame)
            temp_frame = None

        case "POPFRAME":
            if len(local_frame) == 0:
                Error.error_exit(frameNotExists)
            temp_frame = local_frame.pop()

        case "RETURN":
            if len(call_stack) == 0:
                Error.error_exit(missingValue)
            current_instruction_index = call_stack.pop()

        case "BREAK":
            sys.stderr.write("Current instruction count: " + str(done_instructions) + "\n")


def one_argument_instruction(instruction):
    global data_stack
    global current_instruction_index

    if len(instruction.arg_list) != 1:
        Error.error_exit(xmlStructureSyntaxLex)
    match instruction.opcode.upper():
        case "PUSHS":
            # check fromat
            data_to_push = instruction.arg_list[0].value
            data_stack.append(data_to_push)

        case "POPS":
            if len(data_stack) == 0:
                Error.error_exit(missingValue)
            data_to_pop = data_stack.pop()
            var_to_file = variable_check_and_return(instruction.arg_list[0].value)
            type_to_pop = type(data_to_pop)
            try:
                var_to_file.update_value(instruction.arg_list[0].value, data_to_pop, type_to_pop)
            except(Exception,):
                Error.error_exit(semantics)

        case "DEFVAR":
            execute_defvar(instruction.arg_list[0].value)

        case "CALL":
            call_stack.append(current_instruction_index+1)
            current_instruction_index = labels_ordered[instruction.arg_list[0].value]

        case "LABEL":
            pass
            # already done, check if done correctly

        case "JUMP":
            current_instruction_index = labels_ordered[instruction.arg_list[0].value]

        case "DPRINT":
            # symbol check format
            if instruction.arg_list[0].val_type == "var":
                obj_to_print = variable_check_and_return(instruction.arg_list[0].value)
                data_from_obj = obj_to_print.value
            else:
                data_from_obj = symbol_check_and_return(instruction.arg_list[0].value)
            sys.stderr.write(data_from_obj.value)

        case "WRITE":
            # symbol check format
            if instruction.arg_list[0].val_type == "var":
                obj_to_write = variable_check_and_return(instruction.arg_list[0].value)
                data_from_obj = obj_to_write.value
            else:
                data_from_obj = instruction.arg_list[0].value
            sys.stdout.write(data_from_obj)

        case "EXIT":
            # check format
            if int(instruction.arg_list[0].value) not in range(0, 50):
                Error.error_exit(wrongOperandType)
            sys.exit(int(instruction.arg_list[0].value))


def two_argument_instruction(instruction):
    if len(instruction.arg_list) != 2:
        Error.error_exit(xmlStructureSyntaxLex)
    match instruction.opcode.upper():
        case "MOVE":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                source = variable_check_and_return(instruction.arg_list[1].value)
            else:
                source = symbol_check_and_return(instruction.arg_list[1].value)
            destination.update_value(source.value, source.var_type)

        case "INT2CHAR":
            if instruction.arg_list[0].val_type == "var":
                data_to_convert = variable_check_and_return(instruction.arg_list[1].value)
            else:
                data_to_convert = symbol_check_and_return(instruction.arg_list[1].value)
            try:
                converted = chr(data_to_convert)
            except (Exception,):
                Error.error_exit(wrongStringManipulation)

            destination = variable_check_and_return(instruction.arg_list[0].value)
            destination.update_value(converted, "string")

        case "STRLEN":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            to_check = symbol_check_and_return(instruction.arg_list[1].value)
            if type(to_check) != str:
                Error.error_exit(wrongStringManipulation)
            destination.update_value(len(to_check.value), "int")

        case "TYPE":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            to_type = symbol_check_and_return(instruction.arg_list[1].value)
            if to_type.var_type is not None:
                destination.update_value(to_type.var_type, "string")
            else:
                destination.update_value("", "string")

        case "NOT":
            # finish different types conversion
            destination = variable_check_and_return(instruction.arg_list[0].value)
            to_not = symbol_check_and_return(instruction.arg_list[1].value)
            if to_not.var_type == "bool":
                destination.update_value(not to_not.value, "bool")
            else:
                Error.error_exit(wrongOperandType)

        case "READ":
            # TODO finish type conversion and input reading
            destination = variable_check_and_return(instruction.arg_list[0].value)
            try:
                input_value = input()
            except (Exception,):
                Error.error_exit(internalError)
            # check for type from argument 1 and convert input_value to that type (bool, string, int)
            if destination.var_type == "bool":
                if input_value.upper() == "TRUE":
                    destination.update_value(True, "bool")
                else:
                    destination.update_value(False, "bool")
            elif destination.var_type == "int":
                try:
                    input_value = int(input_value)
                except (Exception,):
                    Error.error_exit(wrongOperandType)
                destination.update_value(input_value, "int")
            elif destination.var_type == "string":
                try:
                    input_value = str(input_value)
                except (Exception,):
                    Error.error_exit(wrongOperandType)
                destination.update_value(input_value, "string")
            else:
                Error.error_exit(wrongOperandValue)


def three_argument_instruction(instruction):
    global current_instruction_index
    if len(instruction.arg_list) != 3:
        Error.error_exit(xmlStructureSyntaxLex)
    match instruction.opcode.upper():
        case "ADD":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1].value)
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2].value)
            if first.var_type == "int" and second.var_type == "int":
                destination.update_value(first.value + second.value, "int")
            else:
                Error.error_exit(wrongOperandType)

        case "SUB":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1].value)
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2].value)
            if first.var_type == "int" and second.var_type == "int":
                destination.update_value(first.value - second.value, "int")
            else:
                Error.error_exit(wrongOperandType)

        case "MUL":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1].value)
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2].value)
            if first.var_type == "int" and second.var_type == "int":
                destination.update_value(first.value * second.value, "int")
            else:
                Error.error_exit(wrongOperandType)

        case "IDIV":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1].value)
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2].value)
            if second.value == 0:
                Error.error_exit(wrongOperandType)
            if first.var_type == "int" and second.var_type == "int":
                destination.update_value(first.value / second.value, "int")
            else:
                Error.error_exit(wrongOperandType)

        case "LT":
            destination = variable_check_and_return(instruction.arg_list[0].value)

            if instruction.arg_list[1].arg_type == instruction.arg_list[2].arg_type:
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1].value)
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2].value)

                if first.value < second.value:
                    destination.update_value(True, "bool")
                else:
                    destination.update_value(False, "bool")
            else:
                Error.error_exit(wrongOperandType)

        case "GT":
            destination = variable_check_and_return(instruction.arg_list[0].value)

            if instruction.arg_list[1].arg_type == instruction.arg_list[2].arg_type:
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1].value)
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2].value)

                if first.value > second.value:
                    destination.update_value(True, "bool")
                else:
                    destination.update_value(False, "bool")
            else:
                Error.error_exit(wrongOperandType)

        case "EQ":
            destination = variable_check_and_return(instruction.arg_list[0].value)

            if instruction.arg_list[1].arg_type == instruction.arg_list[2].arg_type:
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1].value)
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2].value)

                if first.value == second.value:
                    destination.update_value(True, "bool")
                else:
                    destination.update_value(False, "bool")
            else:
                Error.error_exit(wrongOperandType)

        case "AND":
            destination = variable_check_and_return(instruction.arg_list[0].value)

            if instruction.arg_list[1].arg_type == instruction.arg_list[2].arg_type\
                    and instruction.arg_list[1].arg_type == "bool":
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1].value)
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2].value)

                if first.value and second.value:
                    destination.update_value(True, "bool")
                else:
                    destination.update_value(False, "bool")
            else:
                Error.error_exit(wrongOperandType)

        case "OR":
            destination = variable_check_and_return(instruction.arg_list[0].value)

            if instruction.arg_list[1].arg_type == instruction.arg_list[2].arg_type \
                    and instruction.arg_list[1].arg_type == "bool":
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1].value)
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2].value)

                if first.value or second.value:
                    destination.update_value(True, "bool")
                else:
                    destination.update_value(False, "bool")
            else:
                Error.error_exit(wrongOperandType)

        case "STRI2INT":
            destination = variable_check_and_return(instruction.arg_list[0].value)

            if instruction.arg_list[1].arg_type == "string" and instruction.arg_list[2].arg_type == "int":
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1].value)
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2].value)

                if second.value >= len(first.value) or second.value < 0:
                    Error.error_exit(wrongOperandValue)
                else:
                    destination.update_value(ord(first.value[second.value]), "int")
            else:
                Error.error_exit(wrongOperandType)

        case "CONCAT":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].arg_type == "string" and instruction.arg_list[2].arg_type == "string":
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1].value)
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2].value)

                destination.update_value(first.value + second.value, "string")
            else:
                Error.error_exit(wrongOperandType)

        case "GETCHAR":
            destination = variable_check_and_return(instruction.arg_list[0].value)

            if instruction.arg_list[1].arg_type == "string" and instruction.arg_list[2].arg_type == "int":
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1].value)
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2].value)

                if second.value >= len(first.value) or second.value < 0:
                    Error.error_exit(wrongOperandValue)
                else:
                    destination.update_value(first.value[second.value], "string")
            else:
                Error.error_exit(wrongOperandType)

        case "SETCHAR":
            destination = variable_check_and_return(instruction.arg_list[0].value)

            if instruction.arg_list[1].arg_type == "int" and instruction.arg_list[2].arg_type == "string":
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1].value)
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2].value)

                if first.value >= len(destination.value) or first.value < 0:
                    Error.error_exit(wrongOperandValue)
                else:
                    destination.update_value(destination.value[:first.value] + second.value[0]
                                                + destination.value[first.value+1:], "string")
            else:
                Error.error_exit(wrongOperandType)

        case "JUMPIFEQ":
            if instruction.arg_list[1].arg_type == instruction.arg_list[2].arg_type:
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1].value)
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2].value)

                if first.value == second.value:
                    current_instruction_index = labels_ordered[instruction.arg_list[0].value]
            else:
                Error.error_exit(wrongOperandType)

        case "JUMPIFNEQ":
            if instruction.arg_list[1].arg_type == instruction.arg_list[2].arg_type:
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1].value)
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2].value)

                if first.value != second.value:
                    current_instruction_index = labels_ordered[instruction.arg_list[0].value]

            else:
                Error.error_exit(wrongOperandType)


def check_labels(list_to_check):
    labels = []
    for instruction in list_to_check:
        if instruction.opcode == "LABEL":
            label_name = instruction.arg_list[0].value
            if label_name in labels:
                Error.error_exit(semantics)
            labels.append(label_name)

        elif instruction.opcode != "LABEL":
            for argument in instruction.arg_list:
                if argument.val_type == "label":
                    if argument.value not in labels:
                        Error.error_exit(semantics)


def interpret_code(instruction_list, input_data):
    global current_instruction_index
    global done_instructions
    while current_instruction_index < len(instruction_list):
        instruction = instruction_list[current_instruction_index]
        current_instruction_index += 1
        done_instructions += 1
        name_to_call = instruction.opcode.upper()
        if name_to_call in ("CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK"):
            no_argument_instruction(instruction)

        elif name_to_call in ("PUSHS", "POPS", "DEFVAR", "CALL",
                                        "LABEL", "JUMP", "DPRINT", "WRITE", "EXIT"):
            one_argument_instruction(instruction)

        elif name_to_call in ("MOVE", "INT2CHAR", "STRLEN", "TYPE", "NOT", "READ"):
            two_argument_instruction(instruction)

        elif name_to_call in ("ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "NOT",
                                        "STRI2INT", "CONCAT", "GETCHAR", "SETCHAR", "JUMPIFEQ", "JUMPIFNEQ"):
            three_argument_instruction(instruction)

        else:
            Error.error_exit(wrongOperandType)


def main():
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
        one_line = "".join(source_file_split)
        root = ET.fromstring(one_line)
    except(Exception,):
        Error.error_exit(xmlStructureSyntaxLex)

    instruction_list = load_xml_to_list(root)
    check_labels(instruction_list)
    interpret_code(instruction_list, input_file_split)


if __name__ == '__main__':
    main()
