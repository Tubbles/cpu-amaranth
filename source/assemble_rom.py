#!/usr/bin/env python3

import argparse
from codes import Operation, Argument
import re


def parse_tokens(token_list):
    byte_list = []
    labels = {}
    deferred_tokens = []

    while len(token_list):
        token = token_list.pop(0)

        if token.endswith(":"):
            label = token.strip(":")
            labels[label] = len(byte_list)

        elif token == ".byte":
            token = token_list.pop(0)
            while token != "\n":
                byte_list.append(int(token, 0))
                print(f"0 Assembled: {int(token, 0)} (from {token})")
                token = token_list.pop(0)

        elif token.upper() in Operation.members():
            byte_list.append(int(Operation.get(token.upper())))
            print(f"1 Assembled: {int(Operation.get(token.upper()))} (from {token})")

        elif token.upper() in Argument.members():
            byte_list.append(Argument.REG)
            print(f"2 Assembled: {Argument.REG} (from {token})")
            byte_list.append(int(Argument.get(token.upper())))
            print(f"3 Assembled: {int(Argument.get(token.upper()))} (from {token})")

        elif token[0] == "#":
            byte_list.append(Argument.IMM)
            print(f"4 Assembled: {Argument.IMM} (from {token})")
            byte_list.append(int(token[1:], 0))
            print(f"5 Assembled: {int(token[1:], 0)} (from {token})")

        elif token[0] == "[" and token[1] != "#" and token[-1] == "]" and token[1:-1].upper() in Argument.members():
            byte_list.append(Argument.IND)
            print(f"6 Assembled: {Argument.IND} (from {token})")
            byte_list.append(int(Argument.get(token[1:-1].upper())))
            print(f"7 Assembled: {int(Argument.get(token[1:-1].upper()))} (from {token})")

        elif token[0] == "[" and token[1] == "#" and token[-1] == "]":
            byte_list.append(Argument.RAM)
            print(f"8 Assembled: {Argument.RAM} (from {token})")
            byte_list.append(int(token[2:-1], 0))
            print(f"9 Assembled: {int(token[2:-1], 0)} (from {token})")

        elif token == "\n":
            # TODO : Write out the args param when it has been refactored
            pass

        elif token in labels:
            byte_list.append(Argument.IMM)
            print(f"10 Assembled: {Argument.IMM} (from {token})")
            byte_list.append(labels[token])
            print(f"11 Assembled: {labels[token]} (from {token})")

        else:
            # raise Exception(f"Unknown token: #{token}#")
            # Unknown token, defer it for later (if it is eg. a future label) and add a placeholder
            byte_list.append(Argument.IMM)
            print(f"12 Assembled: {Argument.IMM} (from {token})")
            deferred_tokens.append((len(byte_list), token))
            byte_list.append(0)
            print(f"13 Assembled: {0} (deferred token) (from {token})")

    # Check the deferred tokens
    for (offset, token) in deferred_tokens:
        if token in labels:
            byte_list[offset] = labels[token]
            print(f"14 Assembled deferred token at {offset}: {labels[token]} (from {token})")
        else:
            raise Exception(f"Unknown token: #{token}#")

    # Fix up the numbers
    for index in range(len(byte_list)):
        if byte_list[index] < 0:
            byte_list[index] = 256 + byte_list[index]
        if byte_list[index] > 255:
            byte_list[index] = 255 & byte_list[index]

    # Add final halt if needed
    if byte_list[-1] != Operation.HALT:
        byte_list.append(int(Operation.HALT))

    # print(labels)
    # print(byte_list)
    print(f"Assembled {len(byte_list)} bytes")
    return bytes(byte_list)
    # return byte_list


def tokenize(s):
    tokens = []

    for line in s:
        line_tokens = line
        line_tokens = line_tokens.split(";")[0]
        line_tokens = line_tokens.strip()
        line_tokens = re.split(r" |\t", line_tokens)
        line_tokens.append("\n")
        if len(line_tokens) > 0:
            tokens += list(filter(lambda s: s != "", line_tokens))
    return tokens


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", nargs=1)
    ap.add_argument("-o", "--output", nargs=1)
    args = ap.parse_args()

    with open(args.input[0], "r") as ifs:
        tokens = tokenize(ifs.readlines())
        with open(args.output[0], "wb") as ofs:
            ofs.write(parse_tokens(tokens))
