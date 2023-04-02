#!/usr/bin/env python3

import sys
import argparse
import xml.etree.ElementTree as ET
import re



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

    print(arg_list)
    return arg_list

if __name__ == '__main__':
    argus = parse_arguments()
    print(len(argus))


