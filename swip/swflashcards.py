#!python3

"""Generate html for printing flash cards from sign puddle export"""

import io
import bisect

import os
import json
import argparse

import xml.etree.ElementTree as ET

from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import quote_plus

from . import compose

ET.register_namespace("", "http://www.w3.org/2000/svg")
DICTAPI_URL = "https://api.datamuse.com/words?sp={:}&md=f"


class NoGlossesError (ValueError):
    """A sign puddle markup language entry had no valid glosses."""


class Sign:
    def __init__(self, sign, glosses, comment=None, source=None):
        self.sign_string = sign
        self.glosses = glosses
        self.comment = comment
        self.source = source

    @classmethod
    def from_spml_entry(cl, spml_entry):
        data = spml_entry.findall("term")
        glosses = [element.text for element in data[1:]]
        if not glosses:
            raise NoGlossesError
        sign = cl(data[0].text, glosses)

        comment = spml_entry.find("text")
        if comment is not None:
            sign.comment = comment.text

        source = spml_entry.find("src")
        if source is not None:
            sign.source = source.text

        return sign

    def __repr__(self):
        return "<Sign {:}>".format(self.glosses[0].upper())


def look_up_frequency(gloss):
    dictapi = DICTAPI_URL.format(quote_plus(gloss))
    gloss_dict = urlopen(dictapi).read().decode('utf-8')

    freq = None
    if ' ' in gloss:
        parts = gloss.split(" ")
        freq = sum(look_up_frequency(part) or 0.0
                   for part in parts)/len(parts)
    elif '-' in gloss:
        parts = gloss.split("-")
        freq = sum(look_up_frequency(part) or 0.0
                   for part in parts)/len(parts)

    parsed = json.loads(gloss_dict)
    if not parsed or parsed[0]["word"] != gloss.lower():
        return freq

    this_freq = float([
        f for f in parsed[0]['tags']
        if f.startswith('f:')][0][2:])
    freq = this_freq if not freq or this_freq > freq else freq
    return freq


def parse_spml(spml_file, signs=None, scores=None, scorer=look_up_frequency, debug=False):
    if signs is None:
        signs = []
    if scores is None:
        scores = [0 for sign in signs]
    rejected = []
    strange = []

    tree = ET.parse(spml_file)
    root = tree.getroot()
    for entry in root.findall("entry"):
        try:
            sign = Sign.from_spml_entry(entry)
        except NoGlossesError:
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

        if is_strange:
            strange.append(sign)
        else:
            index = bisect.bisect(scores, frequency)
            scores.insert(index, frequency)
            signs.insert(index, sign)

    if debug:
        return signs, strange, rejected
    else:
        return signs, strange


def main():
    """Run the CLI"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "spml_file",
        nargs='+',
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
    args = parser.parse_args()

    # Read a cache file of gloss scores
    score_cache = json.load(args.gloss_scores)
    def scorer(gloss):
        try:
            return score_cache[gloss]
        except KeyError:
            score = look_up_frequency(gloss)
            score_cache[gloss] = score
            return score

    # Read all signs from a spml file
    try:
        signs = []
        scores = []
        strange = []
        for file in args.spml_file:
            _, strange_here = parse_spml(file, signs, scores, scorer)
            strange += strange_here
    except KeyboardInterrupt:
        pass

    # Try to write-back a file of gloss scores
    args.gloss_scores.close()
    try:
        with open(args.gloss_scores.name, "w") as json_data:
            json.dump(score_cache, json_data)
    except OSError:
        pass


    # HTML Template
    COLUMNS = 4

    STYLE = """
    tr { page-break-inside: avoid; }
    td { height: 4.5cm; width: %fcm; text-align: center; border: 0.3pt solid black; page-break-inside: avoid; }
    svg { max-width: 100%%; max-height: 4.5cm; overflow: hidden; }
    p { max-width: 100%%; max-height: 4.5cm; overflow: hidden; }
    """ % (18 / COLUMNS)

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
        for i, sign in enumerate(signs + strange):
            if i % COLUMNS == 0:
                # Start a new row
                row_f = ET.SubElement(table_f, 'tr')
                row_b = ET.SubElement(table_b, 'tr')
                print(i)

            cell_f = ET.SubElement(row_f, 'td')
            cell_b = ET.Element('td')
            row_b.insert(0, cell_b)

            # Front contains svg graphic
            svg = ET.parse(io.StringIO(compose.glyphogram(
                sign.sign_string,
                bound=None))).getroot()
            svg.attrib['viewbox'] = "0 0 {:} {:}".format(
                svg.attrib['width'], svg.attrib['height'])
            cell_f.insert(0, svg)

            # Back contains gloss
            ET.SubElement(cell_b, 'p').text = '; '.join(sign.glosses)
        i += 1
    except KeyboardInterrupt:
        pass

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
