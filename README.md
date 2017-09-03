# SignWriting Images in Python

SWIP is an independent Python implementation of the svg generation
procedure of SignWriting Icon Server (written in PHP), which powers
SignPuddle and Wikimedia SL projects. You can find the SWIS source
repository [on github](https://github.com/Slevinski/swis).

The code in this repository is available under MIT license.

For access to the glyphs, you need to download a SignWriting font
database containing the SVG fonts. By default, the software assumes
that it can find the SW font `font_svg1` in an SQLite database
residing in the package root. For other use cases, you have to adapt
`iswa_font.py`. You can download such a font database (under the SIL
Open Font Licence) from http://signpuddle.net/iswa/#fonts, for example
the [Complete Database](http://signpuddle.net/iswa/iswa_full_sql3.zip)
containing also several other fonts.

In order to generate SignWriting SVG images, install the swip package
(`python setup.py`) and run `swip` with the SW string as command line
argument, forwarding stdout into a file, such as

```
$ swip M40x69S35000n18xn18S30c00n18xn18S14c2017x15S22e0420x51 > SCHLECHT.svg
```

## Unsafe Code Warning

Due to the current implementation of ISWA databases, the program needs
to pass a table name to an SQLite query at some point. This insertion
is currently utterly unguarded against SQL injections. Do not use this
program online without knowing what you are doing, even less so with
user-supplied font names!

In a slightly less dangerous fashion, SVG code generated is not
cleanly validated and may be subject to XSS attacks or similar, if SVG
snippets are not from a trusted source.

# swflashcards
This project comes with a small script to generate HTML for printing
flash cards from a SignPuddle SPML export. Go to a SignPuddle
dictionary's Export pane, download "Export source Entire Puddle" which
gives you a file like `sgn53.spml` containing some kind of badly
structured xml. Then,

```
$ swflashcards sgn53.spml
```

will generate two html files called `sgn53_f.html` (containing the
SignWriting images) and `sgn53_b.html` (containing glosses and
comments). The two tables are horizontal mirror images of each other,
so you can print alternating pages of each on front and back sides
(flipping on long edge) to generate flash cards.
