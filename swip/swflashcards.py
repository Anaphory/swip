#!python3

import io
import bisect

import sys
import json
import base64

import xml.etree.ElementTree as ET

from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import quote_plus

import swip.compose

ET.register_namespace("", "http://www.w3.org/2000/svg")
DICTAPI_URL = "https://api.datamuse.com/words?sp={:}&md=f"

class UncleanEntryError (ValueError):
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
            raise UncleanEntryError
        sign = cl(data[0].text, glosses)

        comment = entry.find("text")
        if comment is not None:
            if comment.text[0] == 'M' and comment.text[4] == 'x':
                raise UncleanEntryError
            sign.comment = comment.text

        source = entry.find("src")
        if source is not None:
            sign.source = source.text

        return sign

    def __repr__(self):
        return "<Sign {:}>".format(self.glosses[0].upper())


try:
    cached_glosses
except NameError:
    try:
        with open('gloss_freqs.json') as json_data:
            cached_glosses = json.load(json_data)
    except FileNotFoundError:
        cached_glosses = {}


def look_up_frequency(gloss):
    print(gloss)
    if gloss in cached_glosses:
        return cached_glosses[gloss]
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
        cached_glosses[gloss] = freq
        return cached_glosses[gloss]

    this_freq = float([
        f for f in parsed[0]['tags']
        if f.startswith('f:')][0][2:])
    freq = this_freq if not freq or this_freq > freq else freq
    cached_glosses[gloss] = freq
    return freq


try:
    cached_images
except NameError:
    cached_images = {}


def generate_sign(string):
    if string in cached_images:
        image = cached_images[string]
    else:
        try:
            with open(string + '.png', 'rb') as localfile:
                raw = localfile.read()
        except (FileNotFoundError, OSError):
            raw = urlopen(SIGN_URL.format(string)).read()
            try:
                with open(string + '.png', 'wb') as localfile:
                    localfile.write(raw)
            except OSError:
                pass
        image = cached_images[string] = (
            base64.b64encode(raw).decode("ascii"))
        cached_images[string] = image
    return "data:image/png;base64,{:}".format(image)


rejected = []
strange = []

frequencies = []
signs_by_frequency = []

try:
    for FILE in sys.argv[1:]:
        tree = ET.parse(FILE)
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
                    frequency -= look_up_frequency(gloss)
                    is_strange = False
                except TypeError:
                    pass

            if is_strange:
                strange.append(sign)
            else:
                index = bisect.bisect(frequencies, frequency)
                frequencies.insert(index, frequency)
                signs_by_frequency.insert(index, sign)
except KeyboardInterrupt:
    pass

with open('gloss_freqs.json', "w") as json_data:
    json.dump(cached_glosses, json_data)

strange = sorted(strange, key=lambda x: len(x.glosses[0]))

COLUMNS=5

OUTFILE_f = (FILE[:-5] if FILE.endswith(".spml") else FILE) + "_f.html"
OUTFILE_b = (FILE[:-5] if FILE.endswith(".spml") else FILE) + "_b.html"

STYLE = """
tr {{ page-break-inside: avoid; }}
td {{ height: {length:f}cm; width: {length:f}cm; max-height: {length:f}cm; text-align: center; border: 0.3pt solid black; page-break-inside: avoid; overflow: hidden; }}
svg {{ max-width: {length:f}cm; max-height: {length:f}cm; overflow: hidden; }}
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

try:
    for i, sign in enumerate(signs_by_frequency + strange):
        if i % COLUMNS == 0:
            # Start a new row
            row_f = ET.SubElement(table_f, 'tr')
            row_b = ET.SubElement(table_b, 'tr')
            print(i)

        try:
            image_src = generate_sign(sign.sign_string)
        except HTTPError:
            rejected.append(sign)
            cell_f = ET.SubElement(row_f, 'td')
            cell_b = ET.Element('td')
            row_b.insert(0, cell_b)
            continue

        cell_f = ET.SubElement(row_f, 'td')
        svg = ET.parse(io.StringIO(swip.compose.glyphogram(
            sign.sign_string,
            bound=None))).getroot()
        svg.attrib['viewbox'] = "0 0 {:} {:}".format(
            svg.attrib['width'], svg.attrib['height'])
        cell_f.insert(0, svg)

        cell_b = ET.Element('td')
        row_b.insert(0, cell_b)
        ET.SubElement(cell_b, 'p').text = '; '.join(sign.glosses)
        if sign.comment:
            ET.SubElement(cell_b, 'p', **{'class': 'comment'}).text = sign.comment

    i += 1
except KeyboardInterrupt:
    pass


while i % COLUMNS != 0:
    cell_f = ET.SubElement(row_f, 'td')
    cell_b = ET.Element('td')
    row_b.insert(0, cell_b)
    i += 1

document_f.write(OUTFILE_f)
document_b.write(OUTFILE_b)

