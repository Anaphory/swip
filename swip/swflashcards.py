#!python3

"""Generate html for printing flash cards from sign puddle export"""

import io
import bisect

import os
import sys
import json
import argparse

import xml.etree.ElementTree as ET

from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import quote_plus

from . import compose

ET.register_namespace("", "http://www.w3.org/2000/svg")
DICTAPI_URL = "https://api.datamuse.com/words?sp={:}&md=f"

class UncleanEntryError (ValueError):
    """A sign puddle markup language entry had no valid glosses."""


class Sign:
    def __init__(self, sign, glosses, comment=None, source=None):
        self.sign_string = sign
        self.glosses = tuple(glosses)
        self.comment = comment
        self.source = source

    @classmethod
    def from_spml_entry(cl, spml_entry):
        data = spml_entry.findall("term")
        glosses = [element.text for element in data[1:]]
        if not glosses:
            raise UncleanEntryError
        sign = cl(data[0].text, glosses)

        comment = spml_entry.find("text")
        if comment is not None:
            if comment.text[0] == 'M' and comment.text[4] == 'x':
                raise UncleanEntryError
            sign.comment = comment.text

        source = spml_entry.find("src")
        if source is not None:
            sign.source = source.text

        return sign

    def __repr__(self):
        return "<Sign {:}>".format(self.glosses[0].upper())


def look_up_frequency(gloss):
    """Load frequency data from Datamuse

    >>> look_up_frequency("apple")
    19.314666
    >>> look_up_frequency("juice")
    17.828465
    >>> look_up_frequency("apple-juice") == 0.5 * (
    ... look_up_frequency("apple")+look_up_frequency("juice"))
    True
    """
    dictapi = DICTAPI_URL.format(quote_plus(gloss))
    gloss_dict = urlopen(dictapi).read().decode('utf-8')

    freq = None
    if ' ' in gloss:
        parts = gloss.split(" ")
        freq = sum(look_up_frequency(part) or 0.0
                   for part in parts) / len(parts)
    elif '-' in gloss:
        parts = gloss.split("-")
        freq = sum(look_up_frequency(part) or 0.0
                   for part in parts) / len(parts)

    parsed = json.loads(gloss_dict)
    if not parsed or parsed[0]["word"] != gloss.lower():
        return freq

    this_freq = float([
        f for f in parsed[0]['tags']
        if f.startswith('f:')][0][2:])
    freq = this_freq if not freq or this_freq > freq else freq
    return freq


def parse_spml(spml_file, signs_by_gloss=None, ordered_glosses=None, scores=None, scorer=look_up_frequency, debug=False):
    if signs_by_gloss is None:
        signs_by_gloss = {}
        ordered_glosses = []
    if scores is None:
        scores = [0 for sign in signs_by_gloss]
    rejected = []
    strange = []

    tree = ET.parse(spml_file)
    root = tree.getroot()
    for entry in root.findall("entry"):
        try:
            sign = Sign.from_spml_entry(entry)
        except UncleanEntryError:
            rejected.append(entry)
            continue

        frequency = 0.0
        is_strange = True
        for gloss in sign.glosses:
            try:
                # Make sure that the rarest words are at the end of the list.
                frequency -= scorer(gloss)
                is_strange = False
            except TypeError:
                pass

        if sign.glosses in signs_by_gloss:
            if len(sign.sign_string) > len(signs_by_gloss[sign.glosses].sign_string):
                # Assume longer sign means more detailed transcription means better
                strange.append(signs_by_gloss[sign.glosses])
                signs_by_gloss[sign.glosses] = sign
            else:
                # Duplicate gloss
                strange.append(sign)
        elif is_strange:
            strange.append(sign)
        else:
            index = bisect.bisect(scores, frequency)
            scores.insert(index, frequency)
            signs_by_gloss[sign.glosses] = sign
            ordered_glosses.insert(index, sign.glosses)

    if debug:
        return signs_by_gloss, strange, rejected
    else:
        return signs_by_gloss, strange


def main():
    """Run the CLI"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "spml_file",
        nargs='+',
        type=argparse.FileType('r'),
        help='SPML file(s) to parse')
    parser.add_argument(
        "--gloss-scores",
        type=argparse.FileType('r'),
        help="JSON file with cached gloss scores")
    parser.add_argument(
        "--front",
        type=argparse.FileType('wb'),
        help="HTML file to write signs to")
    parser.add_argument(
        "--back",
        type=argparse.FileType('wb'),
        help="HTML file to write glosses to")
    parser.add_argument(
        "--columns",
        type=int,
        default=5,
        help="Print this many columns of cards per row")
    args = parser.parse_args()

    if args.front is None:
        name = args.spml_file[0].name
        args.front = open(
            (name[:-5] if name.endswith('.spml') else name) +
            '_f.html', 'wb')
    if args.back is None:
        name = args.front.name
        args.back = open(
            (name[:-7] if name.endswith('_f.html') else
             name[:-5] if name.endswith('.html') else name) +
            '_b.html', 'wb')

    # Read a cache file of gloss scores
    if args.gloss_scores:
        score_cache = json.load(args.gloss_scores)
    else:
        score_cache = {}

    def scorer(gloss):
        print(gloss, file=sys.stderr)
        try:
            return score_cache[gloss]
        except KeyError:
            score = look_up_frequency(gloss)
            score_cache[gloss] = score
            return score

    # Read all signs from a spml file
    try:
        signs = {}
        glosses = []
        scores = []
        strange = []
        for file in args.spml_file:
            _, strange_here = parse_spml(file, signs, glosses, scores, scorer)
            strange += strange_here
    except KeyboardInterrupt:
        pass

    # Try to write-back a file of gloss scores
    try:
        args.gloss_scores.close()
        with open(args.gloss_scores.name, "w") as json_data:
            json.dump(score_cache, json_data, sort_keys=True, indent=4)
    except (AttributeError, OSError):
        pass

    # HTML Template
    COLUMNS = args.columns

    STYLE = """
    tr {{ page-break-inside: avoid; max-height: {length:f}cm; overflow: hidden; }}
    td {{ height: {length:f}cm; width: {length:f}cm; border: 0.3pt solid black; page-break-inside: avoid; }}
    svg {{ max-width: {length:f}cm; max-height: {length:f}cm; overflow: hidden; }}
    td div {{ max-width: {length:f}cm; max-height: {length:f}cm; text-align: center; overflow: hidden; }}
    p {{ max-width: {length:f}cm; max-height: {length:f}cm; overflow: hidden; }}
    p.comment {{ font-size: 0.5em; }}
    """.format(length=18/COLUMNS)

    html_f = ET.Element('html')
    document_f = ET.ElementTree(html_f)
    style_f = ET.SubElement(html_f, 'style')
    style_f.text = STYLE
    body_f = ET.SubElement(html_f, 'body')
    table_f = ET.SubElement(body_f, 'table')

    html_b = ET.Element('html')
    document_b = ET.ElementTree(html_b)
    style_b = ET.SubElement(html_b, 'style')
    style_b.text = STYLE
    body_b = ET.SubElement(html_b, 'body')
    table_b = ET.SubElement(body_b, 'table')

    # Generate HTML
    strange = sorted(strange, key=lambda x: len(x.glosses[0]))
    try:
        for i, sign in enumerate([signs[g] for g in glosses] + strange):
            if i % COLUMNS == 0:
                # Start a new row
                row_f = ET.SubElement(table_f, 'tr')
                row_b = ET.SubElement(table_b, 'tr')
                print(i, file=sys.stderr)

            cell_f = ET.SubElement(row_f, 'td')
            cell_b = ET.Element('td')
            row_b.insert(0, cell_b)

            # Front contains svg graphic
            try:
                svg = ET.parse(io.StringIO(compose.glyphogram(
                    sign.sign_string,
                    bound=None))).getroot()
                svg.attrib['viewbox'] = "0 0 {:} {:}".format(
                    svg.attrib['width'], svg.attrib['height'])
                cell_f.insert(0, svg)
            except ValueError:
                # Leave cell blank
                pass

            # Back contains gloss
            maxsize = ET.SubElement(cell_b, 'div')
            ET.SubElement(maxsize, 'p').text = '; '.join(sign.glosses)
            if sign.comment:
                ET.SubElement(maxsize, 'p', **{'class': 'comment'}).text = sign.comment
    except KeyboardInterrupt:
        pass

    i += 1
    # Fill up last row, so that mirror symmetry is given
    while i % COLUMNS != 0:
        cell_f = ET.SubElement(row_f, 'td')
        cell_b = ET.Element('td')
        row_b.insert(0, cell_b)
        i += 1

    # Write output to files
    document_f.write(args.front)
    document_b.write(args.back)

if __name__ == '__main__':
    main()
