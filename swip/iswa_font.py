#!/usr/bin/env python

"""iswa_font: International SignWriting Alphabet font interface

The iswa_font module provides a class for accessing SVG ISWA glyphs
from their location in an SQLite3 database.

"""

import os
import sqlite3

LICENSE = "MIT"
AUTHORS = ["G. A. Kaiping <g.a.kaiping@hum.leidenuniv.nl>"]
COPYRIGHT = "Copyright (c) 2017 Gereon Kaiping"


class ISWAFont:
    """A class encapsulating an ISWA font database connection."""
    def __init__(self, db=None, name="font_svg1"):
        if db is None:
            db = os.path.join(
                os.path.dirname(__file__),
                'iswa.sql3')
        conn = sqlite3.connect(db)
        self.name = name
        self.c = conn.cursor()

    @staticmethod
    def code(symbol_key):
        """Create the internal database code from a symbol key.

        >>> ISWAFont.code('10000')
        1

        >>> ISWAFont.code('S10001')
        2

        >>> ISWAFont.code('S1000f')
        16

        >>> ISWAFont.code('S10100')
        97
        """

        if symbol_key.startswith('S'):
            symbol_key = symbol_key[1:]
        return 1 + (
            (int(symbol_key[0:3], 16) - 256) * 96 +
            int(symbol_key[3:5], 16))


    def svg_snippet(self, symbol):
        """Get an SVG glyph snippet from the database.

        Load the svg group representing the glyph 'key' from the
        database. Return the svg group, its width and height.

        >>> ISWAFont().svg_snippet('S1000f')[1:]
        (30, 21)

        """
        # WARNING: This function is in theory able to run HAVOC with
        # the database, because poor database design means we need to
        # handle IN PRINCIPLE ARBITRAY TABLE NAMES.
        query = (
            'SELECT glyph, w, h FROM {name:s}, symbol '
            'WHERE {name:s}.code = ? '
            'AND symbol.code = ?').format(name=self.name)

        code = self.code(symbol)
        self.c.execute(query, (code, code))
        glyph, w, h = self.c.fetchone()
        return glyph, w, h


    def complete_svg(self, symbol):
        """Load the image corresponding to `key` from the database.

        >>> iswa = ISWAFont()
        >>> print(iswa.complete_svg('S1000f')) # doctest: +NORMALIZE_WHITESPACE +REPORT_NDIFF
        <?xml version="1.0" standalone="no"?>
        <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20010904//EN" "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">
        <svg version="1.0" xmlns="http://www.w3.org/2000/svg width="30" height="21">
        <metadata>S1000f</metadata>
        <g transform="scale(0.938 0.913) translate(10.667 -9) rotate(315) scale(-1,1)">
            <rect id="index" x="13" y="0" width="2" height="15" fill="#000000" />
            <rect id="base" x="0" y="15" width="15" height="15" fill="#000000" />
            <rect id="fill" x="2" y="17" width="11" height="11" fill="#ffffff" />
        </g>
        </svg>

        """
        if symbol.startswith('S'):
            symbol = symbol[1:]

        glyph, w, h = self.svg_snippet(symbol)

        return """<?xml version="1.0" standalone="no"?>
        <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20010904//EN"
        "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">
        <svg version="1.0" xmlns="http://www.w3.org/2000/svg width="{w:d}" height="{h:d}">
        <metadata>S{symbol:s}</metadata>
        {glyph:s}
        </svg>
        """.format(
            w=w, h=h, symbol=symbol, glyph=glyph)
