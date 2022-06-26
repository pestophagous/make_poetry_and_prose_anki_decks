#!/usr/bin/python3

import os
import pprint
import string

IN_FILE = '/tmp/text.txt'

PP = pprint.PrettyPrinter(indent=4)


def process_one_line(line):
    return line.translate(str.maketrans('', '', string.punctuation)).strip()


def get_processed_lines(filename):
    """
    get all lines. skip empty lines. strip punctuation.
    number the lines.
    prepend START_OF_TEXT, append END_OF_TEXT.
    """
    result = []
    with open(filename) as file:
        for line in file:
            p = process_one_line(line)
            if len(p) > 0:
                result += [p]

    i = 0
    for line in result:
        i += 1
        result[i - 1] = str(i) + ': ' + result[i - 1]

    return ['START_OF_TEXT'] + result + ['END_OF_TEXT']


def initialize(line):
    result = ''
    tokens = line.split()
    for t in tokens:
        if str(t[0]).isnumeric():
            result += t
        else:
            result += t[0]

        result += ' '

    return result.strip()


def get_single_quiz_item(prefix_line, target_line, suffix_line):
    return {
        'prompt':
        prefix_line + '\n' + initialize(target_line) + '\n' + suffix_line,
        'answer':
        target_line
    }


def get_quiz_items_from_processed_lines(processed_lines):
    assert len(processed_lines
               ) >= 3, "need at least 3 lines; each quiz item uses 3 lines"

    result = []
    for i in range(1, len(processed_lines) - 1):
        result += [
            get_single_quiz_item(processed_lines[i - 1], processed_lines[i],
                                 processed_lines[i + 1])
        ]

    return result


def main():
    o = get_processed_lines(IN_FILE)
    qo = get_quiz_items_from_processed_lines(o)
    PP.pprint(qo)


if __name__ == '__main__':
    main()
