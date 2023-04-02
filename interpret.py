#!/usr/bin/env python3

import sys
import argparse
import xml.etree.ElementTree as ET
import re


class Argument:
    def __init__(self, type, name="",  order=0):
        self.name = name
        self.type = type
        self.order = int(order)

    def __str__(self):
        if self.name:
            return self.name
        else:
            if self.type:
                return f" <{self.type}>"
            else:
                return ""

    def __eq__(self, other):

        if self.type == other.type:
            return True
        elif "symb" == self.type:
            if other.type in ("var", "string", "int", "bool", "nil"):
                return True
        elif "symb" == other.type:
            if self.type in ("var", "string", "int", "bool", "nil"):
                return True
        elif "type" == self.type:
            if other.type in ("string", "int", "bool"):
                return True
        elif "type" == other.type:
            if self.type in ("string", "int", "bool"):
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

    print(arg_list)
    return arg_list


if __name__ == '__main__':
    argus = parse_arguments()

    print(len(argus))


