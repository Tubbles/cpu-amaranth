#!/usr/bin/env python3

import argparse
from codes import Operation
import re


def parse_tokens(token_list):
    byte_list = []
    labels = {}

    while len(token_list):
        token = token_list.pop(0)

        if token.endswith(":"):
            label = token.strip(":")
            labels[label] = len(byte_list)

        elif token == ".byte":
            token = token_list.pop(0)
            while token != "\n":
                byte_list.append(int(token, 0))
                token = token_list.pop(0)

        elif token.upper() in [op.name for op in Operation]:
            byte_list.append(int(Operation[token.upper()].value))

        elif token == "\n":
            pass

        else:
            # Unknown token
            raise Exception(f"Unknown token: {token}")

    # print(labels)
    return bytes(byte_list)


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
