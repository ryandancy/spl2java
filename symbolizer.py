"""
Transforms SPL code into symbols.
"""

DEBUG = False # if True, print debug messages


import re
from splerror import SplError


# symbolization constants
SYM_IGNORE = -1
SYM_CHARACTER = 0
SYM_END_PUNCTUATION = 1 # i.e. '!' or '.'
SYM_COMMA = 2
SYM_QUESTION_MARK = 3
SYM_COLON = 4
SYM_OPEN_STAGE_DIRECTION = 5 # '['
SYM_CLOSE_STAGE_DIRECTION = 6 # ']'
SYM_STAGE_DIRECTION_ENTER = 7
SYM_STAGE_DIRECTION_EXIT = 8
SYM_STAGE_DIRECTION_EXEUNT = 9
SYM_AND = 10
SYM_ACT = 11
SYM_SCENE = 12
SYM_ROMAN_NUMERAL = 13
SYM_ASSIGNMENT = 14 # i.e. are, art, is, am, etc.
SYM_AS = 15 # 'as' - for after assignments
SYM_SUM = 16
SYM_DIFFERENCE = 17
SYM_PRODUCT = 18
SYM_QUOTIENT = 19
SYM_REMAINDER = 20
SYM_TWICE = 21
SYM_THRICE = 22
SYM_SQUARE = 23
SYM_CUBE = 24
SYM_HALF = 25
SYM_SQUARE_ROOT = 26
SYM_CUBE_ROOT = 27
SYM_IF_SO = 28
SYM_IF_NOT = 29
SYM_JUMP = 30 # let us return, let us proceed, etc.
SYM_ZERO = 31 # i.e. zero, nothing, etc.
SYM_POSITIVE_NOUN = 32 # nouns with a value of 1
SYM_NEGATIVE_NOUN = 33 # nouns with a value of -1
SYM_ADJECTIVE = 34
SYM_GREATER_THAN = 35 # i.e. better than, etc.
SYM_LESS_THAN = 36 # i.e. worse than, etc.
SYM_PUSH_TO_STACK = 37 # i.e. remember
SYM_POP_FROM_STACK = 38 # i.e. recall
SYM_INPUT_NUMBER = 39 # listen to your/thy heart
SYM_INPUT_CHARACTER = 40 # open your/thy mind
SYM_OUTPUT_NUMBER = 41 # open your/thy heart
SYM_OUTPUT_CHARACTER = 42 # speak your/thy mind
SYM_1ST_PERSON_PRONOUN = 43 # i.e. I, me, myself, etc.
SYM_2ND_PERSON_PRONOUN = 44 # i.e. thou, thyself, you, yourself, etc.

# lists of tokens that constitute certain symbols

def read_nouns(filename):
    # if a noun starts with '*' we don't add 's' on the end, else we do
    with open('wordlists/' + filename, 'r') as nouns_file:
        nouns = map(str.strip, nouns_file.readlines())
        return tuple(list(map(lambda noun: noun[1:] if noun.startswith('*') else noun, nouns))
                     + [noun + 's' for noun in nouns if not noun.startswith('*')])

POSITIVE_NOUNS = read_nouns('positive-nouns.txt')
NEGATIVE_NOUNS = read_nouns('negative-nouns.txt')

def read_list_file(filename):
    with open('wordlists/' + filename, 'r') as file_:
        return tuple(map(str.strip, file_.readlines()))

ADJECTIVES = read_list_file('adjectives.txt')
FIRST_PERSON_PRONOUNS = read_list_file('first-person-pronouns.txt')
SECOND_PERSON_PRONOUNS = read_list_file('second-person-pronouns.txt')

ASSIGNMENTS = read_list_file('equal.txt')

GREATER = read_list_file('greater.txt')
LESSER = read_list_file('lesser.txt')

ZERO = read_list_file('zero.txt')

# this gigantic dict maps a list of tokens to symbols they should be translated to
TOKENS_TO_SYMBOLS = {
    ('.', '!'): (SYM_END_PUNCTUATION,),
    (',',): (SYM_COMMA,),
    ('?',): (SYM_QUESTION_MARK,),
    (':',): (SYM_COLON,),
    ('[',): (SYM_OPEN_STAGE_DIRECTION,),
    (']',): (SYM_CLOSE_STAGE_DIRECTION,),
    ('enter',): (SYM_STAGE_DIRECTION_ENTER,),
    ('exit',): (SYM_STAGE_DIRECTION_EXIT,),
    ('exeunt',): (SYM_STAGE_DIRECTION_EXEUNT,),
    ('and',): (SYM_AND,),
    ('act',): (SYM_ACT,),
    ('scene',): (SYM_SCENE,),
    ASSIGNMENTS: (SYM_ASSIGNMENT,),
    ('as',): (SYM_AS,),
    ('sum',): (SYM_SUM,),
    ('difference',): (SYM_DIFFERENCE,),
    ('product',): (SYM_PRODUCT,),
    ('quotient',): (SYM_QUOTIENT,),
    ('remainder',): (SYM_REMAINDER,),
    ('twice',): (SYM_TWICE,),
    ('thrice',): (SYM_THRICE,),
    ('half',): (SYM_HALF,),
    ('square',): (SYM_SQUARE,),
    ('cube',): (SYM_CUBE,),
    ZERO: (SYM_ZERO,),
    POSITIVE_NOUNS: (SYM_POSITIVE_NOUN,),
    NEGATIVE_NOUNS: (SYM_NEGATIVE_NOUN,),
    ADJECTIVES: (SYM_ADJECTIVE,),
    GREATER: (SYM_GREATER_THAN,),
    LESSER: (SYM_LESS_THAN,),
    ('remember',): (SYM_PUSH_TO_STACK,),
    ('recall',): (SYM_POP_FROM_STACK,),
    FIRST_PERSON_PRONOUNS: (SYM_1ST_PERSON_PRONOUN,),
    SECOND_PERSON_PRONOUNS: (SYM_2ND_PERSON_PRONOUN,),
}

# tokens that must be in order to constitute a symbol
MULTI_TOKENS_TO_SYMBOLS = {
    ('if', 'so'): (SYM_IF_SO,),
    ('if', 'not'): (SYM_IF_NOT,),
    ('listen', 'to', 'your', 'heart'): (SYM_INPUT_NUMBER,),
    ('listen', 'to', 'thy', 'heart'): (SYM_INPUT_NUMBER,),
    ('open', 'your', 'mind'): (SYM_INPUT_CHARACTER,),
    ('open', 'thy', 'mind'): (SYM_INPUT_CHARACTER,),
    ('open', 'your', 'heart'): (SYM_OUTPUT_NUMBER,),
    ('open', 'thy', 'heart'): (SYM_OUTPUT_NUMBER,),
    ('speak', 'your', 'mind'): (SYM_OUTPUT_CHARACTER,),
    ('speak', 'thy', 'mind'): (SYM_OUTPUT_CHARACTER,),
    ('let', 'us', 'return'): (SYM_JUMP,),
    ('let', 'us', 'proceed'): (SYM_JUMP,),
    ('we', 'must', 'return'): (SYM_JUMP,),
    ('we', 'must', 'proceed'): (SYM_JUMP,),
    ('we', 'shall', 'return'): (SYM_JUMP,),
    ('we', 'shall', 'proceed'): (SYM_JUMP,),
    ('square', 'root'): (SYM_SQUARE_ROOT,),
    ('cube', 'root'): (SYM_CUBE_ROOT,),
}

with open('wordlists/characters.txt', 'r') as characters_file:
    # characters go in either one depending on whether or not they have spaces
    all_characters = map(str.strip, characters_file.readlines())
    for character in all_characters:
        if ' ' in character:
            nospaces = ''.join(character.split()) # remove all whitespace
            MULTI_TOKENS_TO_SYMBOLS[tuple(character.lower().split())] = (SYM_CHARACTER, nospaces)
        else:
            TOKENS_TO_SYMBOLS[(character.lower(),)] = (SYM_CHARACTER, character)

MULTI_TOKENS = list(MULTI_TOKENS_TO_SYMBOLS.keys())


def tokenize(spl):
    """
    Tokenize the SPL source into a list of tokens. Tokens are contiguous letters
    or individual non-letter characters. Whitespace is filtered out.
    :param spl: The SPL source code to tokenize.
    :returns: A list of tokens present in the SPL source.
    """

    # Do initial splitting using regex
    # Not using re.split() because it doesn't split on zero-length matches
    tokens = re.sub(r'(?<=[^\-\w])|(?=[^\-\w])', '\f', spl).split('\f')

    # Filter whitespace
    tokens = list(filter(lambda token: not token.isspace(), tokens))

    return tokens


romans =  'MDCLXVI' # for order
no_doubles = 'DLV'
doubleable = 'MCXI'
roman_to_int = {'M': 1000, 'D': 500, 'C': 100, 'L': 50, 'X': 10, 'V': 5, 'I': 1}

def translate_roman_numeral(token):
    """
    Attempt to translate a Roman numeral into an integer.
    :param token: The token (possibly) representing a Roman numeral.
    :returns: The integer represented by the Roman numeral, or False if it is not a Roman numeral.
    """

    if token == '':
        raise ValueError

    # damn that's a big algorithm
    try:
        n = 0
        last_value = -1
        double_run = 0
        added_before = set() # to prevent things like 'XIX'
        subtracted_last = False
        
        for i, c in reversed(list(enumerate(token))):
            value = roman_to_int[c]
            if value > last_value:
                # in order: addition
                n += value
                double_run = 0
                added_before.add(c)
                subtracted_last = False
            elif value == last_value:
                # a double character: ok up to 4 for CXI, never ok for DLV, always ok for M, never ok when subtracting
                if c in no_doubles or (double_run >= 3 and c != 'M') or subtracted_last:
                    raise ValueError
                else:
                    n += value
                    double_run += 1
                    subtracted_last = False
            else:
                # out of order: probably subtraction
                # make sure it's only 1 roman numeral 'less' than the previous one
                if (c not in no_doubles and c not in added_before
                        and (romans.index(c)-1 == romans.index(token[i+1]) or doubleable.index(c)-1 == doubleable.index(token[i+1]))):
                    # good: subtract
                    n -= value
                    subtracted_last = True
                else:
                    # improper roman numeral
                    raise ValueError
                double_run = 0
            last_value = value
        return n
    except (KeyError, ValueError):
        raise ValueError('Not a valid Roman numeral')


def symbolize(tokens):
    """
    Transform a list of tokens into a list of symbols. Symbols are tuples in the
    form of (SYM_X, data, ...) in which SYM_X is a symbol identifier constant.
    :param tokens: The list of tokens to symbolize.
    :returns: The list of tokens transformed into a list of symbols.
    """

    symbols = []

    for i, token in enumerate(tokens):
        lowercase = token.lower() # for case-insensitive symbols
        foundit = False # for continuing the outer loop
        
        # multi-token symbols
        for multi_token in MULTI_TOKENS:
            if i < len(multi_token) - 1:
                continue # not enough tokens to possibly be this multi token

            # select the n tokens behind this one, including this one
            possible_multi_token = tokens[i-len(multi_token)+1:i+1]

            # convert to tuple and lowercase everything
            possible_multi_token = tuple(map(str.lower, possible_multi_token))

            if possible_multi_token == multi_token:
                # we found it - remove the last n-1 symbols and add the new one
                del symbols[-len(multi_token)+1:]
                symbols.append(MULTI_TOKENS_TO_SYMBOLS[multi_token])
                foundit = True
                if DEBUG:
                    print('m', MULTI_TOKENS_TO_SYMBOLS[multi_token], multi_token)
                break
        if foundit:
            continue

        # translate single-word tokens defined in TOKENS_TO_SYMBOLS to their respective symbols
        for token_list, symbol in TOKENS_TO_SYMBOLS.items():
            if lowercase in token_list:
                if lowercase == 'i':
                    # special case: "I" is ambiguous
                    # figure out if it's the pronoun I or a Roman numeral
                    # if the last non-IGNORE symbol is "act" or "scene" it's a Roman numeral, else the pronoun
                    try:
                        last_sym = next(sym for sym in reversed(symbols) if sym[0] != SYM_IGNORE)[0]
                        if last_sym in (SYM_ACT, SYM_SCENE):
                            # interpret as Roman numeral
                            symbols.append((SYM_ROMAN_NUMERAL, 1))
                            if DEBUG:
                                print('r', token, 1, 'note: interpreted as Roman numeral')
                        else:
                            # interpret as pronoun
                            symbols.append((SYM_1ST_PERSON_PRONOUN,))
                            if DEBUG:
                                print('s', (SYM_1ST_PERSON_PRONOUN,), token, FIRST_PERSON_PRONOUNS[0], 'note: interpreted as pronoun')
                    except StopIteration:
                        # there are only IGNOREs before it: it's at the beginning of the program, ignore it
                        symbols.append((SYM_IGNORE,))
                    
                    foundit = True
                    break

                symbols.append(symbol)
                if DEBUG:
                    print('s', symbol, token, token_list[0])
                foundit = True
                break
        if foundit:
            continue

        # translate Roman numerals
        try:
            num = translate_roman_numeral(token)
            symbols.append((SYM_ROMAN_NUMERAL, num))
            if DEBUG:
                print('r', token, num)
            continue
        except ValueError:
            # not a Roman numeral: carry on
            pass

        # it's not a recognized symbol
        symbols.append((SYM_IGNORE,))

    return symbols
