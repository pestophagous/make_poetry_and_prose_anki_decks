#!/usr/bin/python3

import argparse
import os
import pprint
import string
import json
import urllib.request

IN_FILE = '/tmp/text.txt'

PP = pprint.PrettyPrinter(indent=4)


def process_one_line(line):
    tostrip = string.punctuation
    tostrip = tostrip.replace('<', '')
    tostrip = tostrip.replace('>', '')
    return line.translate(str.maketrans('', '', tostrip)).strip()


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
        elif t[0] == '<' and t[-1] == '>':
            result += '&lt;' + t[1:-1] + '&gt;'
        else:
            result += t[0]

        result += ' '

    return result.strip().lower()


def get_single_quiz_item(prefix_line, target_line, suffix_line):
    return {
        'prompt':
        prefix_line + '<br>' +
            initialize(target_line) + '<br>' + suffix_line,
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
    parser.add_argument("deckname")
    args = parser.parse_args()

    o = get_processed_lines(IN_FILE)
    qo = get_quiz_items_from_processed_lines(o)
    PP.pprint(qo)

    ankiconn_invoke('createDeck', deck=args.deckname)
    add_items_to_deck(qo, args.deckname)

    names = ankiconn_invoke('deckNames')
    PP.pprint(names)


if __name__ == '__main__':
    main()
