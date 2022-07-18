#!/usr/bin/python3

import argparse
import json
import os
import pprint
import string
import sys
import urllib.request


PP = pprint.PrettyPrinter(indent=4)


class Phrase:
    def __init__(self, num, rawtextline):
        self.linenum = num
        self.rawtext = rawtextline
        self.processedtext = Phrase.process_one_line(rawtextline)

    def line_with_full_annotation(self):
        if self.linenum is not None:
            return str(self.linenum) + ": " + self.processedtext
        else:
            return self.rawtext

    def cryptic_initialized_line(self):
        return Phrase.initialize(self.line_with_full_annotation())

    def is_discardable(self):
        return len(self.processedtext) < 1

    def process_one_line(line):
        tostrip = string.punctuation
        tostrip = tostrip.replace('<', '')
        tostrip = tostrip.replace('>', '')
        return line.translate(str.maketrans('', '', tostrip)).strip()

    def initialize(line):
        result = ''
        tokens = line.split()
        for t in tokens:
            if str(t[0]).isnumeric():
                result += t
            elif t[0] == '<' and t[-1] == '>':
                result += '&lt;' + t[1:-1] + '&gt;'
            else:
                result += t[0]

            result += ' '

        return result.strip().lower()


def get_processed_lines(filename):
    """
    get all lines. skip empty lines. strip punctuation.
    number the lines.
    prepend START_OF_TEXT, append END_OF_TEXT.
    """
    result = []
    i = 1
    with open(filename) as file:
        for line in file:
            p = Phrase(i, line)
            if False == p.is_discardable():
                result += [p]
                i += 1

    return [Phrase(None, 'START_OF_TEXT')] + result + [Phrase(None, 'END_OF_TEXT')]


def get_single_quiz_item(prefix_line, target_line, suffix_line):
    return {
        'prompt':
        prefix_line.line_with_full_annotation() + '<br>' +
        target_line.cryptic_initialized_line() +
        '<br>' + suffix_line.line_with_full_annotation(),
        'answer':
        target_line.line_with_full_annotation()
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


def ankiconn_make_request(action, **params):
    return {'action': action, 'params': params, 'version': 6}


def ankiconn_invoke(action, **params):
    requestJson = json.dumps(ankiconn_make_request(action,
                                                   **params)).encode('utf-8')
    response = json.load(
        urllib.request.urlopen(
            urllib.request.Request('http://localhost:8765', requestJson)))
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def add_items_to_deck(quiz_items, deckname):
    for qi in quiz_items:
        ankiconn_invoke('addNote', note={'deckName': deckname, 'modelName': 'Basic', 'fields': {
            'Front': qi['prompt'], 'Back': qi['answer']}})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--shortcircuit', action='store_true',
                        help="only creates stimuli structures; does not upload to anki")
    parser.add_argument("deckname")
    parser.add_argument("inputfile")
    args = parser.parse_args()

    o = get_processed_lines(args.inputfile)
    qo = get_quiz_items_from_processed_lines(o)
    PP.pprint(qo)

    if args.shortcircuit:
        sys.exit(0)

    ankiconn_invoke('createDeck', deck=args.deckname)
    add_items_to_deck(qo, args.deckname)

    names = ankiconn_invoke('deckNames')
    PP.pprint(names)


if __name__ == '__main__':
    main()
