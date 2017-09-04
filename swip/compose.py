#!/urs/bin/env python

"""image: Compose symbols to SignWriting SVGs

The core function is `glyphogram`, which takes a KSW string (and some
optional parameters) and constructs a SVG graphic for that sign.

"""

from . import parser
from .iswa_font import ISWAFont

DEFAULT = ISWAFont()

symbol_group_color = {
    'hand': '#0000ff',
    'movement': '#ff0000',
    'dynamics': '#ff00ff',
    'head': '#00ff00',
    'trunk': '#000000',
    'limb': '#000000',
    'location': '#ddaa00',
    'punctuation': '#ff5500'}


def glyphogram(ksw_string, pad=1, bound=None, line='#000000',
               fill='#ffffff', colorize=False, font=DEFAULT):
    """
    >>> print(glyphogram(
    ...  'M40x69S35000n18xn18S30c00n18xn18S14c2017x15S22e0420x51'))
    ... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <?xml version="1.0" standalone="no"?>
    <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20010904//EN" "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">
        <svg version="1.0" xmlns="http://www.w3.org/2000/svg" width="60.000000" height="89.000000">
        <metadata>
            Generated with SWIP using Valerie Sutton's ISWA 2010 symbols (font_svg1)
            M40x69S35000n18xn18S30c00n18xn18S14c2017x15S22e0420x51
        </metadata>
        <g transform="translate(1,1)"> ...
        </g>
    </svg>
    """

    # Process cluster string
    layout = parser.parse(ksw_string)
    x_max, y_max = layout[0][1]
    x_min, y_min = parser.min_coordinates(layout, False)

    # Crudely center the image
    if bound == 'c' or bound == 'h':
        if -x_min > x_max:
            x_max = -x_min
        else:
            x_min = -x_max
    if bound == 'c' or bound == 'h':
        if -x_min > x_max:
            x_max = -x_min
        else:
            x_min = -x_max

    # Pad with whitespace
    x_max += pad
    x_min -= pad
    y_max += pad
    y_min -= pad

    # Load images and put in the right places
    images = []
    for num, (symbol, (x, y)) in enumerate(layout):
        if num == 0:
            continue
        key = symbol[1:6]
        if colorize:
            group = parser.symbol_type(symbol)
            line = symbol_group_color[group]
        images.append("""
        <g transform="translate({x:d},{y:d})">
            {core:}
        </g>""".format(
            x=x - x_min,
            y=y - y_min,
            core=font.glyph(key, line, fill)))

    # Insert into single SVG canvas
    svg = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20010904//EN" "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">
    <svg version="1.0" xmlns="http://www.w3.org/2000/svg" width="{width:f}" height="{height:f}">
    <metadata>
        Generated with SWIP using Valerie Sutton's ISWA 2010 symbols ({font:})
        {ksw_string:s}
    </metadata>
    {image:s}
    </svg>
    """.format(
        font=font.name,
        width=x_max - x_min,
        height=y_max - y_min,
        ksw_string=ksw_string,
        image=''.join(images))

    # Return
    return svg
