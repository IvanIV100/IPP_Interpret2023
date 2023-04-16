#!/usr/bin/env python3
import sys
import argparse
import xml.etree.ElementTree as ET
import re

# Global variables
global_frame = {}
local_frame = []
temp_frame = None
input_file_split = []
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
            Error.error_exit(thirtytwo)
        self.opcode = opcode.upper()
        self.arg_list = arg_list
        if order:
            try:
                self.order = int(order)
            except (Exception,):
                Error.error_exit(ninetynine)
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


ten = Error("Missing parameter or illegal combination\n", 10)
eleven = Error("Cannot open source files\n", 11)
twelve = Error("Cannot open files to write\n", 12)
ninetynine = Error("Internal error\n", 99)
thirtyone = Error("Wrong XML syntax, not well formatted\n", 31)
thirtytwo= Error("Wrong XML structure or syntactic/lexical error\n", 32)
fiftytwo = Error("Semantics error, e.g. not defined label or redefinition of label\n", 52)
fiftythree = Error("Wrong operand type\n", 53)
fiftyfour = Error("Accessing not defined variable, frame exists\n", 54)
fiftyfive = Error("Frame not exists\n", 55)
fiftysix = Error("Missing value in variable or stack\n", 56)
fiftyseven = Error("Wrong operand value, e.g. division by zero\n", 57)
fiftyeight = Error("Wrong string manipulation\n", 58)


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
        Error.error_exit(ten)

    return arguments.source, arguments.input


def split_to_lines(file):
    if file:
        try:
            with open(file, "r") as in_file:
                data_lines = [line.strip() for line in in_file.readlines()]
                in_file.close()
        except (Exception,):
            Error.error_exit(eleven)

    else:
        return None
    return data_lines


def check_xml_start(root):
    if root.tag != "program":
        Error.error_exit(thirtytwo)
    if root.attrib["language"].upper() != "IPPcode23".upper():
        Error.error_exit(thirtytwo)
    for att in root.attrib:
        if att not in ["language", "name", "description"]:
            Error.error_exit(thirtytwo)


def load_xml_to_list(root):
    list_parsed = []
    for child in root:
        if child.tag != "instruction":
            Error.error_exit(thirtytwo)
        # instruction check
        child_arguments = []
        # maybe missing check xml arg order correct
        for each in child:
            for att in each.attrib:
                if att != "type":
                    Error.error_exit(thirtytwo)
                matched = re.search("^arg([1-3])$", each.tag)
                if matched:
                    order_num = each.tag.replace("arg", "")
                    argument = Argument(each.get("type"), each.text, order_num)
                    child_arguments.append(argument)
        child_arguments.sort(key=lambda argument: argument.order)
        for index, argument in enumerate(child_arguments, start=1):
            if argument.order < 1:
                Error.error_exit(thirtytwo)
            if argument.order != index:
                Error.error_exit(thirtytwo)
        instruction = Instruction(child.get("opcode"), child_arguments, child.get("order"))
        list_parsed.append(instruction)

    list_parsed.sort(key=lambda instruction: instruction.order)
    instruction_order_list = []
    for instruction in list_parsed:
        if instruction.order in instruction_order_list:
            Error.error_exit(thirtytwo)
        else:
            instruction_order_list.append(instruction.order)
        if instruction.order is None:
            Error.error_exit(thirtytwo)
        if int(instruction.order) < 1:
            Error.error_exit(thirtytwo)

    return list_parsed


# check if type matches with value
def symbol_check_and_return(symbol):
    output = None
    type_symbol = symbol.val_type
    val = symbol.value
    output = Variable(None, val, type_symbol)
    return output


def variable_check_and_return(variable):
    global global_frame
    global local_frame
    global temp_frame
    to_return = None
    split_frame_name = variable.split("@")
    if len(split_frame_name) != 2:
        Error.error_exit(fiftythree)
    frame = variable.split("@")[0]
    name = variable.split("@")[1]

    match frame:
        case "GF":
            if name not in global_frame:
                Error.error_exit(fiftyfour)
            else:
                to_return = global_frame[name]

        case "LF":
            if len(local_frame) == 0:
                Error.error_exit(fiftyfive)
            if name not in local_frame[-1]:
                Error.error_exit(fiftyfour)
            else:
                to_return = local_frame[-1][name]

        case "TF":
            if not temp_frame:
                Error.error_exit(fiftyfive)
            if name not in temp_frame:
                Error.error_exit(fiftyfour)
            else:
                to_return = temp_frame[name]
    if not to_return:
        Error.error_exit(fiftytwo)
    else:
        return to_return


def execute_defvar(to_define):
    global global_frame
    global local_frame
    global temp_frame

    # add check for format
    frame = to_define.split("@")[0]
    name = to_define.split("@")[1]

    match frame:
        case "GF":
            if name not in global_frame:
                global_frame[name] = Variable(name, None, None)
            else:
                Error.error_exit(fiftytwo)

        case "LF":
            if name not in local_frame[-1]:
                local_frame[-1][name] = Variable(name, None, None)
            else:
                Error.error_exit(fiftytwo)

        case "TF":
            if not temp_frame:
                Error.error_exit(fiftyfive)
            if name not in temp_frame:
                temp_frame[name] = Variable(name, None, None)
            else:
                Error.error_exit(fiftytwo)


def no_argument_instruction(instruction):
    global temp_frame
    global local_frame
    global call_stack
    global current_instruction_index
    global done_instructions

    if len(instruction.arg_list) != 0:
        Error.error_exit(thirtytwo)

    match instruction.opcode.upper():
        case "CREATEFRAME":
            temp_frame = []

        case "PUSHFRAME":
            if not temp_frame:
                Error.error_exit(fiftyfive)

            # fix this
            for each in temp_frame:
                name_in_temp = variable_check_and_return(each)
                new_name = "LF@" + each.split("@")[1]
                new_var = Variable(new_name, name_in_temp.value, name_in_temp.val_type)
                local_frame.append(new_var)
            temp_frame = None

        case "POPFRAME":
            if len(local_frame) == 0:
                Error.error_exit(fiftyfive)
            temp_frame = local_frame.pop(-1)

        case "RETURN":
            if len(call_stack) == 0:
                Error.error_exit(fiftysix)
            current_instruction_index = call_stack.pop(-1)

        case "BREAK":
            sys.stderr.write("Current instruction count: " + str(done_instructions) + "\n")


def one_argument_instruction(instruction):
    global data_stack
    global current_instruction_index
    global labels_ordered
    global call_stack

    if len(instruction.arg_list) != 1:
        Error.error_exit(thirtytwo)

    match instruction.opcode.upper():
        case "PUSHS":
            # check fromat
            if instruction.arg_list[0].val_type == "var":
                data_to_push = variable_check_and_return(instruction.arg_list[0].value)
            else:
                data_to_push = symbol_check_and_return(instruction.arg_list[0])
            data_to_push_new = Variable(None, data_to_push.value, data_to_push.var_type)
            data_stack.append(data_to_push_new)

        case "POPS":
            if len(data_stack) == 0:
                Error.error_exit(fiftysix)
            data_to_pop = data_stack.pop(-1)
            var_to_file = variable_check_and_return(instruction.arg_list[0].value)
            var_to_file.update_value(data_to_pop.value, data_to_pop.var_type)

        case "DEFVAR":
            execute_defvar(instruction.arg_list[0].value)

        case "CALL":
            call_stack.append(current_instruction_index)
            current_instruction_index = labels_ordered[str(instruction.arg_list[0].value)]

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
                data_from_obj = symbol_check_and_return(instruction.arg_list[0])
            sys.stderr.write(data_from_obj.value)

        case "WRITE":
            # symbol check format
            if instruction.arg_list[0].val_type == "var":
                obj_to_write = variable_check_and_return(instruction.arg_list[0].value)
            else:
                obj_to_write = symbol_check_and_return(instruction.arg_list[0])

            data_from_obj = str(obj_to_write.value)
            print(data_from_obj, end="")

        case "EXIT":
            # check format
            try:
                int(instruction.arg_list[0].value)
            except(Exception,):
                Error.error_exit(fiftythree)

            if int(instruction.arg_list[0].value) not in range(0, 50):
                Error.error_exit(fiftyseven)
            sys.exit(int(instruction.arg_list[0].value))


def two_argument_instruction(instruction, input_data):
    if len(instruction.arg_list) != 2:
        Error.error_exit(thirtytwo)
    match instruction.opcode.upper():
        case "MOVE":
            destination = variable_check_and_return(instruction.arg_list[0].value)

            if instruction.arg_list[1].val_type == "var":
                source = variable_check_and_return(instruction.arg_list[1].value)
            else:
                source = symbol_check_and_return(instruction.arg_list[1])
            destination.update_value(source.value, source.var_type)

        case "INT2CHAR":
            if instruction.arg_list[0].val_type == "var":
                data_to_convert = variable_check_and_return(instruction.arg_list[1].value)
            else:
                data_to_convert = symbol_check_and_return(instruction.arg_list[1])
            try:
                converted = chr(int(data_to_convert.value))
            except (Exception,):
                # fix other err code
                Error.error_exit(fiftythree)

            destination = variable_check_and_return(instruction.arg_list[0].value)
            destination.update_value(converted, "string")

        case "STRLEN":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                to_check = variable_check_and_return(instruction.arg_list[1].value)
            else:
                to_check = symbol_check_and_return(instruction.arg_list[1])
            if to_check.var_type != "string":
                Error.error_exit(fiftythree)
            try:
                str_len = len(to_check.value)
            except (Exception,):
                Error.error_exit(fiftyseven)
            destination.update_value(str_len, "int")

        case "TYPE":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                to_type = variable_check_and_return(instruction.arg_list[1].value)
            else:
                to_type = symbol_check_and_return(instruction.arg_list[1])
            if to_type.var_type is not None:
                destination.update_value(to_type.var_type, "string")
            else:
                destination.update_value("", "string")

        case "NOT":
            # finish different types conversion
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                to_not = variable_check_and_return(instruction.arg_list[1].value)
            else:
                to_not = symbol_check_and_return(instruction.arg_list[1])
            if to_not.var_type == "bool":
                if to_not.value == "true":
                    destination.update_value("false", "bool")
                elif to_not.value == "false":
                    destination.update_value("true", "bool")
            else:
                Error.error_exit(fiftythree)

        case "READ":
            # TODO finish type conversion and input reading
            # mozno double pokus o read z konzoly
            destination = variable_check_and_return(instruction.arg_list[0].value)
            #fix reading from input_data
            try:
                input_value = input_data.pop(0)
            except (Exception,):
                Error.error_exit(fiftyfour)

            # check for type from argument 1 and convert input_value to that type (bool, string, int)
            if str(instruction.arg_list[1].value) == "bool":
                if input_value.upper() == "TRUE":
                    destination.update_value("true", "bool")
                else:
                    destination.update_value("false", "bool")
            elif str(instruction.arg_list[1].value) == "int":
                try:
                    input_value = int(input_value)
                except (Exception,):
                    Error.error_exit(fiftythree)
                destination.update_value(input_value, "int")
            elif str(instruction.arg_list[1].value) == "string":
                try:
                    input_value = str(input_value)
                except (Exception,):
                    Error.error_exit(fiftythree)
                destination.update_value(input_value, "string")
            else:
                Error.error_exit(thirtytwo)


def three_argument_instruction(instruction):
    global current_instruction_index
    if len(instruction.arg_list) != 3:
        Error.error_exit(thirtytwo)
    match instruction.opcode.upper():
        case "ADD":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1])
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2])
            if first.var_type == "int" and second.var_type == "int":
                destination.update_value(first.value + second.value, "int")
            else:
                Error.error_exit(fiftythree)

        case "SUB":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1])
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2])
            if first.var_type == "int" and second.var_type == "int":
                destination.update_value(int(first.value) - int(second.value), "int")
            else:
                Error.error_exit(fiftythree)

        case "MUL":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1])
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2])
            if first.var_type == "int" and second.var_type == "int":
                destination.update_value(int(first.value) * int(second.value), "int")
            else:
                Error.error_exit(fiftythree)

        case "IDIV":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1])
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2])

                # maybe bad error

            if first.var_type == "int" and second.var_type == "int":
                if int(second.value) == 0:
                    Error.error_exit(fiftyseven)
                destination.update_value(int(first.value) / int(second.value), "int")
            else:
                Error.error_exit(fiftythree)

        case "LT":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1])
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2])
            if first.var_type == second.var_type:
                if first.value < second.value:
                    destination.update_value("true", "bool")
                else:
                    destination.update_value("false", "bool")
            else:
                Error.error_exit(fiftythree)

        case "GT":
            destination = variable_check_and_return(instruction.arg_list[0].value)

            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1])
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2])

            if first.var_type == second.var_type:
                if first.value > second.value:
                    destination.update_value("true", "bool")
                else:
                    destination.update_value("false", "bool")
            else:
                Error.error_exit(fiftythree)

        case "EQ":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1])
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2])

            if first.var_type == second.var_type:
                if first.value == second.value:
                    destination.update_value("true", "bool")
                else:
                    destination.update_value("false", "bool")
            else:
                Error.error_exit(fiftythree)

        case "AND":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1])
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2])

            if first.var_type == "bool" and second.var_type == "bool":
                if first.value and second.value:
                    destination.update_value("true", "bool")
                else:
                    destination.update_value("false", "bool")
            else:
                Error.error_exit(fiftythree)

        case "OR":
            destination = variable_check_and_return(instruction.arg_list[0].value)

            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1])
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2])
            if first.var_type != "bool" or second.var_type != "bool":
                Error.error_exit(fiftythree)
            if first.value == "true" or second.value == "true":
                destination.update_value("true", "bool")
            else:
                destination.update_value("false", "bool")

        case "STRI2INT":
            destination = variable_check_and_return(instruction.arg_list[0].value)

            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1])
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2])

            if first.var_type != "string" or second.var_type != "int":
                Error.error_exit(fiftythree)
            if int(second.value) > len(first.value) or int(second.value) < 0:
                Error.error_exit(fiftyeight)
            else:
                value_to_change = ord(first.value[int(second.value)])
                destination.update_value(value_to_change, "int")


        case "CONCAT":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            if instruction.arg_list[1].val_type == "string" and instruction.arg_list[2].val_type == "string":
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1])
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2])

                destination.update_value(first.value + second.value, "string")
            else:
                Error.error_exit(fiftythree)

        case "GETCHAR":
            destination = variable_check_and_return(instruction.arg_list[0].value)
            # fix this with correct var or symbol check and return code
            if instruction.arg_list[1].val_type == "string" and instruction.arg_list[2].val_type == "int":
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1])
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2])

                if int(second.value) >= len(first.value) or int(second.value) < 0:
                    Error.error_exit(fiftyseven)
                else:
                    destination.update_value(first.value[int(second.value)], "string")
            else:
                Error.error_exit(fiftythree)

        case "SETCHAR":
            destination = variable_check_and_return(instruction.arg_list[0].value)

            if instruction.arg_list[1].val_type == "var":
                first = variable_check_and_return(instruction.arg_list[1].value)
            else:
                first = symbol_check_and_return(instruction.arg_list[1])
            if instruction.arg_list[2].val_type == "var":
                second = variable_check_and_return(instruction.arg_list[2].value)
            else:
                second = symbol_check_and_return(instruction.arg_list[2])

            if first.var_type != "int" or second.var_type != "string" or destination.var_type != "string":
                Error.error_exit(fiftythree)
            if int(first.value) >= len(destination.value) or int(first.value) < 0 or destination.value == "":
                Error.error_exit(fiftyeight)
            else:
                destination.update_value(destination.value[:int(first.value)] + second.value[0]
                                            + destination.value[int(first.value)+1:], "string")

        case "JUMPIFEQ":
            if instruction.arg_list[1].val_type == instruction.arg_list[2].val_type:
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1])
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2])

                if first.value == second.value:
                    current_instruction_index = labels_ordered[instruction.arg_list[0].value]
            else:
                Error.error_exit(fiftythree)

        case "JUMPIFNEQ":
            if instruction.arg_list[1].val_type == instruction.arg_list[2].val_type:
                if instruction.arg_list[1].val_type == "var":
                    first = variable_check_and_return(instruction.arg_list[1].value)
                else:
                    first = symbol_check_and_return(instruction.arg_list[1])
                if instruction.arg_list[2].val_type == "var":
                    second = variable_check_and_return(instruction.arg_list[2].value)
                else:
                    second = symbol_check_and_return(instruction.arg_list[2])

                if first.value != second.value:
                    current_instruction_index = labels_ordered[str(instruction.arg_list[0].value)]

            else:
                Error.error_exit(fiftythree)


def check_labels(list_to_check):
    global labels_ordered
    labels = []
    for instruction in list_to_check:
        if instruction.opcode.upper() == "LABEL":
            label_name = instruction.arg_list[0].value
            if label_name in labels:
                Error.error_exit(fiftytwo)
            labels.append(label_name)
            labels_ordered[label_name] = list_to_check.index(instruction)
    for instruction in list_to_check:
        if instruction.opcode.upper() != "LABEL":
            for argument in instruction.arg_list:
                if argument.val_type == "label":
                    if argument.value not in labels:
                        Error.error_exit(fiftytwo)


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
            two_argument_instruction(instruction, input_data)

        elif name_to_call in ("ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "NOT",
                              "STRI2INT", "CONCAT", "GETCHAR", "SETCHAR", "JUMPIFEQ", "JUMPIFNEQ"):
            three_argument_instruction(instruction)

        else:
            Error.error_exit(thirtytwo)


def main():
    global input_file_split
    source_file, input_file = argument_parser()

    if source_file:
        source_file_split = split_to_lines(source_file)
    else:
        # check if reading is correct
        source_file_split = [line.strip for line in sys.stdin]

    if input_file:
        input_file_split = split_to_lines(input_file)
    else:
        input_file_split = [line.strip for line in sys.stdin]

    # fix checking of xml fails
    try:
        string_one = "".join(source_file_split)
        root = ET.fromstring(string_one)
    except(Exception,):
        Error.error_exit(thirtyone)

    # check if xml is correct
    check_xml_start(root)

    instruction_list = load_xml_to_list(root)
    for instruction in instruction_list:
        for argument in instruction.arg_list:
            if argument.val_type == "string":
                escaped_list = re.findall(r'(\\[0-9]{3})+', str(argument.value))

                for escaped_uni in escaped_list:
                    unicode_as_chr = chr(int(escaped_uni[1:]))
                    argument.value = argument.value.replace(escaped_uni, unicode_as_chr)
    check_labels(instruction_list)
    interpret_code(instruction_list, input_file_split)


if __name__ == '__main__':
    main()
