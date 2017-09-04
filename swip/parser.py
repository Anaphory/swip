#!/usr/bin/env python3

"""parser: SignWriting string parse functions

Define various regular expressions and use them to validate
SignWriting strings.

"""

import re

SYMBOL_BLOCK = 'S[123][0-9a-f]{2}[0-5][0-9a-f]'
COORD_BLOCK = 'n?[0-9]+xn?[0-9]+'
POS_COORD_BLOCK = '[0-9]+x[0-9]+'
re_word = (
    '(A(' + SYMBOL_BLOCK + ')+)?'
    '[BLMR](' + SYMBOL_BLOCK + COORD_BLOCK + ')*')
re_pword = (
    '(A(' + SYMBOL_BLOCK + ')+)?'
    '[BLMR](' + SYMBOL_BLOCK + POS_COORD_BLOCK +
    'x' + COORD_BLOCK + ')*')
re_panelword = (
    '[BLMR](' + POS_COORD_BLOCK + ')'
    '(' + SYMBOL_BLOCK + COORD_BLOCK + ')*')
re_lword = (
    '(A(' + SYMBOL_BLOCK + ')+)?' + re_panelword)
re_punc = 'S38[7-9ab][0-5][0-9a-f]'
re_ppunc = re_punc + POS_COORD_BLOCK
re_lpunc = re_punc + COORD_BLOCK

COORDINATES = re.compile(COORD_BLOCK,
                         flags=re.IGNORECASE)
SYM_WITH_COORD = re.compile(SYMBOL_BLOCK + COORD_BLOCK,
                            flags=re.IGNORECASE)
PREFIX = re.compile('A((' + SYMBOL_BLOCK + ')+)',
                    flags=re.IGNORECASE)
RAW_TOKEN = re.compile("(" + re_word + '|' + re_punc + ")",
                       flags=re.IGNORECASE)
EXPANDED_TOKEN = re.compile('(' + re_pword + '|' + re_ppunc + ')',
                            flags=re.IGNORECASE)
LAYOUT_TOKEN = re.compile('(' + re_lword + '|' + re_lpunc + ')',
                          flags=re.IGNORECASE)
PANEL_TOKEN = re.compile(
    'D' + POS_COORD_BLOCK + '(_' + re_panelword + ')*',
    flags=re.IGNORECASE)


# Pattern matching on Kartesian SignWriting strings

def is_raw(text):
    """Test whether text is a raw SignWriting string.

    Returns True if `text` is raw Kartesian SignWriting, that is,
    without symbol sizes or preprocessed information, False otherwise.

    This function tests according to pattern-matching with a regex, so
    it can only be a necessary, not a sufficient condition. For
    example, is_raw('BS3ff5f') will be True, even though the symbol
    slot S3ff5f is not assigned.

    >>> all([is_raw('B'), is_raw('L'), is_raw('M'), is_raw('R')])
    True

    >>> is_raw('BS10000n10xn10')
    True
    >>> is_raw('LS10000n10xn10')
    True
    >>> is_raw('MS10000n10xn10')
    True
    >>> is_raw('RS10000n10xn10')
    True

    >>> is_raw('AS10000BS10000n10xn10')
    True
    >>> is_raw('AS10000LS10000n10xn10')
    True
    >>> is_raw('AS10000MS10000n10xn10')
    True
    >>> is_raw('AS10000RS10000n10xn10')
    True

    >>> is_raw('AS10000BS1000010x10xn10xn10')
    False
    >>> is_raw('AS10000LS1000010x10xn10xn10')
    False
    >>> is_raw('AS10000MS1000010x10xn10xn10')
    False
    >>> is_raw('AS10000RS1000010x10xn10xn10')
    False


    @param `text` str
    @return boolean

    """
    return all([RAW_TOKEN.fullmatch(token) for token in text.split()])


def is_expanded(text):
    """Test if text is Kartesian SignWriting with symbol sizes.

    Returns True if `text` is Kartesian SignWriting with symbol sizes
    specified.

    This function tests according to pattern-matching with a regex, so
    it can only be a necessary, not a sufficient condition. For
    example, is_expanded('BS3ff5f1x1') will be True, even though the
    symbol slot S3ff5f is not assigned.

    >>> all([is_expanded('B'), is_expanded('L'),
    ... is_expanded('M'), is_expanded('R')])
    True

    >>> is_expanded('BS1000010x10xn10xn10')
    True
    >>> is_expanded('LS1000010x10xn10xn10')
    True
    >>> is_expanded('MS1000010x10xn10xn10')
    True
    >>> is_expanded('RS1000010x10xn10xn10')
    True

    >>> is_expanded('AS10000BS1000010x10xn10xn10')
    True
    >>> is_expanded('AS10000LS1000010x10xn10xn10')
    True
    >>> is_expanded('AS10000MS1000010x10xn10xn10')
    True
    >>> is_expanded('AS10000RS1000010x10xn10xn10')
    True

    >>> is_expanded('BS10000n10xn10')
    False
    >>> is_expanded('LS10000n10xn10')
    False
    >>> is_expanded('MS10000n10xn10')
    False
    >>> is_expanded('RS10000n10xn10')
    False

    """
    return all([EXPANDED_TOKEN.fullmatch(token) for token in text.split()])


def is_layouted(text):
    """Test if text is Kartesian SignWriting with layout data.

    Returns True if `text` is Kartesian SignWriting without symbol
    sizes specified, but with layout data from pre-processing.

    This function tests according to pattern-matching with a regex, so
    it can only be a necessary, not a sufficient condition. For
    example, is_raw(BS3ff5f1x1) will be True, even though the symbol
    slot S3ff5f is not assigned.

    >>> all([is_layouted('B10x10'), is_layouted('L3x4'),
    ... is_layouted('M3x2'), is_layouted('R8x23')])
    True

    >>> is_layouted('B10x10S10000n10xn10')
    True
    >>> is_layouted('L10x10S10000n10xn10')
    True
    >>> is_layouted('M10x10S10000n10xn10')
    True
    >>> is_layouted('R10x10S10000n10xn10')
    True

    """
    return all([LAYOUT_TOKEN.fullmatch(token)
                for token in text.split()])


def is_panel(text):
    """Test if text is a Kartesian SignWriting panel string.

    Returns True if `text` is Kartesian SignWriting without symbol
    sizes specified, but with layout data from pre-processing.

    This function tests according to pattern-matching with a regex, so
    it can only be a necessary, not a sufficient condition. For
    example, is_raw(BS3ff5f1x1) will be True, even though the symbol
    slot S3ff5f is not assigned.
    """
    return all([PANEL_TOKEN.fullmatch(token) for token in text.split()])


def all_symbols(sw_string):
    """List all symbols referenced in sw_string

    List all symbols that are referenced in the body of the Kartesian
    SignWriting string `sw_string`, that is, all symbols outside the
    `AS00000` prefix, or equivalently, all symbols with defined
    coordinates.

    >>> all_symbols('BS10000n10xn10')
    ['S10000']

    >>> all_symbols('LS10000n10xn10')
    ['S10000']

    >>> all_symbols('MS10000n10xn10')
    ['S10000']

    >>> all_symbols('RS10000n10xn10')
    ['S10000']

    >>> all_symbols('AS10000BS10000n10xn10S1035f10x10')
    ['S10000', 'S1035f']

    >>> all_symbols('AS10000LS10000n10xn10S1035f10x10')
    ['S10000', 'S1035f']

    >>> all_symbols('AS10000MS10000n10xn10S1035f10x10')
    ['S10000', 'S1035f']

    >>> all_symbols('AS10000RS10000n10xn10S1035f10x10')
    ['S10000', 'S1035f']

    """
    symbols = []
    for group in SYM_WITH_COORD.findall(sw_string):
        symbols.append(group[:6])
    return symbols


def prefix_symbols(sw_string):
    """ List all symbols referenced in the prefix.

    >>> prefix_symbols(
    ... 'M18x33S1870an11x15S18701n18xn10S205008xn4S2e7340xn32')
    []

    >>> prefix_symbols('AS1870aS18701S2e734M18x33S1870an11x15'
    ... 'S18701n18xn10S205008xn4S2e7340xn32')
    ['S1870a', 'S18701', 'S2e734']
    """
    match = PREFIX.match(sw_string)
    if not match:
        return []
    return re.findall(SYMBOL_BLOCK, match.group(0), flags=re.IGNORECASE)


# Define symbol types

symbol_ranges = {
    'iswa': (0x100, 0x38b),
    'writing': (0x100, 0x37e),
    'hand': (0x100, 0x204),
    'movement': (0x205, 0x2f6),
    'dynamics': (0x2f7, 0x2fe),
    'head': (0x2ff, 0x36c),
    'trunk': (0x36d, 0x375),
    'limb': (0x376, 0x37e),
    'location': (0x37f, 0x386),
    'punctuation': (0x387, 0x38b)}


def symbol_id(symbol):
    """This basic shape's integer ID.

    A helper function for looking up symbol types. Following the `S`,
    the first three symbols are the hexadecimal number of the symbol
    (up to rotation or similar variation).

    >>> symbol_id('S10350') == 0x103
    True
    >>> symbol_id('2a6') == 0x2a6
    True

    """
    if symbol.startswith('S'):
        return int(symbol[1:4], 16)
    else:
        return int(symbol[:3], 16)


def is_type(symbol, type):
    """Check whether a symbol is of a given type.

    The symbol can be given as ISWA identifier with or without `S`, or
    as the corresponding integer id of the basic shape.

    >>> is_type('S32a00', 'head')
    True
    >>> is_type(0x389, 'punctuation')
    True
    >>> is_type('1da51', 'hand')
    True

    """
    try:
        symbol = symbol_id(symbol)
    except AttributeError:
        pass
    try:
        return (
            symbol_ranges[type][0] <= symbol <= symbol_ranges[type][1])
    except KeyError:
        raise ValueError('No symbol type {:}.'.format(type))


def symbol_type(symbol):
    """Return the type of the symbol.

    >>> symbol_type(0x100)
    'hand'
    >>> symbol_type('S38b00')
    'punctuation'
    >>> symbol_type('S37e00')
    'limb'

    """

    try:
        symbol = symbol_id(symbol)
    except AttributeError:
        pass
    for type, (lower, upper) in symbol_ranges.items():
        if type == 'iswa' or type == 'writing':
            # Not a fundamental type
            continue
        if lower <= symbol <= upper:
            return type
    raise ValueError('Not a valid symbol: {:}'.format(symbol))


def swnumber(string):
    """Convert a KSW number string into an integer.

    A KSW number string is a string of the format 'n?[0-9]+'. The 'n'
    indicates 'negative' numbers.

    >>> swnumber('0092')
    92
    >>> swnumber('200')
    200
    >>> swnumber('n34')
    -34
    >>> swnumber('-34')
    Traceback (most recent call last):
    [...]
    ValueError: Not a valid KSW number string: -34

    """
    if not re.fullmatch('n?[0-9]+', string):
        raise ValueError('Not a valid KSW number string: {:}'.format(
            string))
    if string.startswith('n'):
        return -int(string[1:])
    else:
        return int(string)


def coordinates(sw_substring):
    """Convert a KSW coordinate string into a pair of integers.

    A KSW coordinate string, used for Cartesian coordinates as well as
    dimensions, is a string of the format 'n?[0-9]+xn?[0-9]+' and
    corresponds in an obvious manner to a pair of signed integers.

    >>> coordinates('0092x0108')
    (92, 108)
    >>> coordinates('n15x20')
    (-15, 20)
    >>> coordinates('1x2x3')
    Traceback (most recent call last):
    [...]
    ValueError: Not a valid KSW coordinates string: 1x2x3

    """
    if not COORDINATES.fullmatch(sw_substring):
        raise ValueError(
            'Not a valid KSW coordinates string: {:}'.format(
                sw_substring))
    first, last = sw_substring.split('x')
    return swnumber(first), swnumber(last)


def parse(layout_string):
    """Parse a layout string to array of symbols with placement.

    >>> parse('M18x33S1870an11x15S18701n18xn10S205008xn4S2e7340xn32')
    [('M', (18, 33)), ('S1870a', (-11, 15)), ('S18701', (-18, -10)), ('S20500', (8, -4)), ('S2e734', (0, -32))]

    >>> parse('MS1870an11x15S18701n18xn10S205008xn4S2e7340xn32')
    [('M', (8, 15)), ('S1870a', (-11, 15)), ('S18701', (-18, -10)), ('S20500', (8, -4)), ('S2e734', (0, -32))]

    >>> parse('S38800n36xn4')
    [('B', (36, 4)), ('S38800', (-36, -4))]

    >>> parse('')
    [('M', (0, 0))]
    """
    if not layout_string:
        return [('M', (0, 0))]

    seq = 'A' + ''.join(prefix_symbols(layout_string))
    sw_string = layout_string.replace(seq, '')

    match = re.fullmatch(
        '((' + re_punc + ')(' + COORD_BLOCK + '))|'
        '([BLMR](' + POS_COORD_BLOCK + ')?)'
        '((' + SYMBOL_BLOCK + COORD_BLOCK + ')*)',
        sw_string)

    if not match:
        raise ValueError(
            'String {:} contained unrecognized elements'.format(
                sw_string))

    if match.group(1):
        # This is a punctuation character
        punct = match.group(2)
        coord = coordinates(match.group(3))
        return [
            ('B', (-coord[0], -coord[1])),
            (punct, coord)]
    else:
        # This is some other character

        cluster = []
        max_x = max_y = float('-inf')
        for symbol in re.findall(
                SYMBOL_BLOCK + COORD_BLOCK,
                match.group(6)):
            coord = coordinates(symbol[6:])
            max_x = max(max_x, coord[0])
            max_y = max(max_y, coord[1])
            cluster.append(
                (symbol[:6], coord))
        cluster.insert(
            0, (match.group(4)[0],
                coordinates(match.group(5)) if match.group(5) else (max_x, max_y)))
        return cluster


def min_coordinates(cluster, min_is_zero=True):
    x_min = 0 if min_is_zero else float('inf')
    y_min = 0 if min_is_zero else float('inf')
    for i, (sym, (x, y)) in enumerate(cluster):
        if i == 0:
            continue
        x_min = min(x_min, x)
        y_min = min(y_min, y)
    return x_min, y_min
