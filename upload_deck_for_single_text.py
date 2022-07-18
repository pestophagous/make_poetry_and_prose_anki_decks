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
    def __init__(self, num, rawtextline, preceder):
        self.linenum = num
        self.rawtext = rawtextline
        self.processedtext = Phrase.process_one_line(rawtextline)

        self.preceding_phrase = preceder
        self.trailing_phrase = None

    def set_trailing_phrase(self, trailer):
        self.trailing_phrase = trailer

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
        for i, t in enumerate(tokens):
            if i == 0 and str(t[0]).isnumeric():
                result += t
            elif str(t).isnumeric():
                result += '#'
            elif t == '-1:':
                result += '&lt;metadata&gt;'
            elif t[0] == '<' and t[-1] == '>':
                result += '&lt;' + t[1:-1] + '&gt;'
            else:
                result += t[0]

            result += ' '

        return result.strip().lower()


class Paragraph:
    def __init__(self, num):
        self.pnum = num
        self.phrases = []
        self.total_paragraphs = -1

    def add_phrase(self, phrase):
        self.phrases += [phrase]

    def is_contentless_boundary_marker(self):
        return self.pnum is None

    def set_total_paragraph_count(self, total):
        self.total_paragraphs = total

    def breadcrumb_text(self):
        return '&lt;p' + str(self.pnum) + '/' + str(self.total_paragraphs) + '&gt;'


def get_processed_lines(filename):
    """
    get all lines. skip empty lines. strip punctuation.
    number the lines.
    prepend START_OF_TEXT, append END_OF_TEXT.
    """
    s_o_t = Phrase(None, 'START_OF_TEXT', None)

    last = s_o_t
    pnum = -1
    result = []
    start_new_p = True
    linenum = -1
    with open(filename) as file:
        for line in file:
            p = Phrase(linenum, line, last)
            if False == p.is_discardable():
                if start_new_p:
                    start_new_p = False
                    pnum += 1
                    result += [Paragraph(pnum)]
                last.set_trailing_phrase(p)
                result[-1].add_phrase(p)
                last = p
                if linenum > 0:
                    linenum += 1
            else:
                if linenum < 0:
                    # (recall that first paragraph is meta-data, not content)
                    linenum = 1  # start numbering lines at SECOND paragraph
                start_new_p = True

    e_o_t = Phrase(None, 'END_OF_TEXT', last)
    last.set_trailing_phrase(e_o_t)

    s_o_t_p = Paragraph(None)
    e_o_t_p = Paragraph(None)
    s_o_t_p.add_phrase(s_o_t)
    e_o_t_p.add_phrase(e_o_t)

    result = [s_o_t_p] + result + [e_o_t_p]
    for rp in result:
        # the -3 is to subtract p0 metadata, then S_O_T and E_O_T
        rp.set_total_paragraph_count(len(result)-3)

    return result


def get_single_quiz_item(target_phrase, enclosing_paragraph):
    return {
        'prompt':
        target_phrase.preceding_phrase.line_with_full_annotation() + '<br>' +
        enclosing_paragraph.breadcrumb_text() +
        target_phrase.cryptic_initialized_line() +
        '<br>' + target_phrase.trailing_phrase.line_with_full_annotation(),
        'answer':
        target_phrase.line_with_full_annotation()
    }


def get_quiz_items_from_processed_lines(paragraphs):
    assert len(paragraphs
               ) >= 3, "need at least 3 paragraphs"

    result = []
    for paragraph in paragraphs:
        if paragraph.is_contentless_boundary_marker():
            continue

        for p in paragraph.phrases:
            result += [
                get_single_quiz_item(p, paragraph)
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
