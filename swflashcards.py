#!python3

import bisect

import sys
import json
import base64

import xml.etree.ElementTree as ET

from urllib.request import urlopen
from urllib.parse import quote_plus
from urllib.error import HTTPError

SIGN_URL = "http://swis.wmflabs.org/glyphogram.php?font=png&text={:}"
DICTAPI_URL = "https://api.datamuse.com/words?sp={:}&md=f"

FILE=sys.argv[1]

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

        comment = entry.find("text")
        if comment is not None:
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
        image = cached_images[string] = (
            base64.b64encode(urlopen(SIGN_URL.format(string)).read()).decode("ascii"))
    return "data:image/png;base64,{:}".format(image)
    

rejected = []
strange = []

frequencies = []
signs_by_frequency = []

tree = ET.parse(FILE)
root = tree.getroot()
try:
    for entry in root.findall("entry"):
        try:
            sign = Sign.from_spml_entry(entry)
        except NoGlossesError:
            rejected.append(entry)
            continue

        frequency = 0.0
        for gloss in sign.glosses:
            try:
                # Make sure that the rarest words are at the end of the list.
                frequency -= look_up_frequency(gloss)
            except TypeError:
                strange.append(sign)

        if frequency:
            index = bisect.bisect(frequencies, frequency)
            frequencies.insert(index, frequency)
            signs_by_frequency.insert(index, sign)
        else:
            strange.append(sign)
except KeyboardInterrupt:
    pass
    
with open('gloss_freqs.json', "w") as json_data:
    json.dump(cached_glosses, json_data)

strange = sorted(strange, key=lambda x: len(x.glosses[0]))

COLUMNS=4

OUTFILE_f = (FILE[:-5] if FILE.endswith(".spml") else FILE) + "_f.html"
OUTFILE_b = (FILE[:-5] if FILE.endswith(".spml") else FILE) + "_b.html"

STYLE = """
tr { page-break-inside: avoid; }
td { height: 5cm; width: %fcm; text-align: center; border: 0.3pt solid black; page-break-inside: avoid; }
img { max-width: 100%%; max-height: 5cm; overflow: hidden}
p { max-width: 100%%; max-height: 5cm; overflow: hidden; }
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

try:
    for i, sign in enumerate(signs_by_frequency + strange):
        if i % COLUMNS == 0:
            # Start a new row
            row_f = ET.SubElement(table_f, 'tr')
            row_b = ET.SubElement(table_b, 'tr')
            print(i)

        cell_f = ET.SubElement(row_f, 'td')
        img_f = ET.SubElement(cell_f, 'img', src=generate_sign(sign.sign_string))


        cell_b = ET.Element('td')
        row_b.insert(0, cell_b)
        ET.SubElement(cell_b, 'p').text = '; '.join(sign.glosses)
except KeyboardInterrupt:
    cell_b = ET.Element('td')
    row_b.insert(0, cell_b)
    
    
i += 1
while i % COLUMNS != 0:
    cell_f = ET.SubElement(row_f, 'td')
    cell_b = ET.Element('td')
    row_b.insert(0, cell_b)
    i += 1
    
document_f.write(OUTFILE_f)
document_b.write(OUTFILE_b)

