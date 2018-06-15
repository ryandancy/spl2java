"""
Does the bulk of the translation work in the SPL -> Java translator.
"""

from splerror import SplError
from symbolizer import *


def skip_as(symbols, symidx):
    """:returns: symidx, 1 after the next 'as'."""
    try:
        symidx += 1
        while symbols[symidx][0] != SYM_AS:
            symidx += 1
        return symidx + 1
    except IndexError:
        raise SplError('No matching "as".')


def skip_till_end_punct(symbols, symidx):
    """:returns: symidx, 1 after the next end punctuation."""
    try:
        symidx += 1 # past this symbol
        while symbols[symidx][0] != SYM_END_PUNCTUATION:
            symidx += 1
        return symidx + 1
    except IndexError:
        raise SplError('End punctuation expected, but none found till end of program.')


def next_is(symbols, symidx, symbol_to_check, msg, increment=True):
    """
    Raise an error if this symbol isn't symbol_to_check.
    :param symbols: The list of symbols.
    :param symidx: The index into the list of symbols.
    :param symbol_to_check: The symbol that this one must be.
    :param msg: The message for the SplError if it is not.
    :param increment: Whether to increment symidx or not.
    :return: symidx, possibly +1
    :raises SplError: if this symbol isn't symbol_to_check.
    """

    if symbols[symidx][0] != symbol_to_check:
        raise SplError(msg)
    return symidx + 1 if increment else symidx


def read_characters(symbols, symidx):
    """
    Read the list of characters from the symbols.
    :param symbols: The list of symbols.
    :param symidx: The index into the list of symbols.
    :returns: A list of characters, and the new symidx.
    :raises SplError: if it's in a bad format or there are duplicate characters.
    """
    
    characters = []
    
    try:
        while symbols[symidx][0] != SYM_ACT:
            # make sure there's a character
            symidx = next_is(symbols, symidx, SYM_CHARACTER, 'Character expected in preamble.', increment=False)

            # make sure it isn't a duplicate
            character = symbols[symidx][1]
            if character in characters:
                raise SplError('Duplicate characters are not allowed.')
            characters.append(character)
            symidx += 1

            # there then has to be a comma
            symidx = next_is(symbols, symidx, SYM_COMMA, 'Comma expected after character in preamble.', increment=False)

            # then eventually there has to be an END_PUNCTUATION
            symidx = skip_till_end_punct(symbols, symidx)
    except IndexError:
        # there are no acts
        raise SplError("You can't just have a play with no acts.")

    return characters, symidx


def parse_header(symbols, symidx, header_symbol, act_counter, scene_counter):
    """
    Parse the act or scene header.
    :param symbols: The list of symbols.
    :param symidx: The index into the list of symbols.
    :param header_symbol: The symbol which constitutes the header (SYM_ACT or SYM_SCENE)
    :param act_counter: The act counter, to make sure the acts are in order/generate the method name.
    :param scene_counter: The scene counter, to make sure the scenes are in order.
    :returns: The name of the act/scene's method, symidx, and act or scene counter.
    :raises SplError: If there is an error.
    """

    counter = act_counter if header_symbol == SYM_ACT else scene_counter

    # first Act or Scene
    if symbols[symidx][0] != header_symbol:
        raise SplError('Expected act or scene keyword.')
    symidx += 1

    # then a Roman numeral
    if symbols[symidx][0] != SYM_ROMAN_NUMERAL:
        raise SplError('Expected Roman numeral after act or scene keyword.')

    # with a valid number according to the counter
    num = symbols[symidx][1]
    if num != counter + 1:
        raise SplError('Act or scene out of order.')
    counter += 1
    symidx += 1

    # then a colon
    if symbols[symidx][0] != SYM_COLON:
        raise SplError('Expected colon after act or scene declaration.')

    # then an arbitrary number of symbols and an END_PUNCTUATION
    try:
        symidx += 1
        while symbols[symidx][0] != SYM_END_PUNCTUATION:
            symidx += 1
    except IndexError:
        raise SplError('Expected end punctuation after act or scene declaration.')

    if header_symbol == SYM_ACT:
        method = 'act' + str(num)
    else:
        method = 'act' + str(act_counter) + 'scene' + str(num)
    return method, symidx + 1, counter


def parse_stage_direction(symbols, symidx, characters, stage):
    """
    Parse a stage direction, making the necessary modifications to the stage.
    :param symbols: The list of symbols.
    :param symidx: The index into the list of symbols.
    :param characters: The list of characters in the program.
    :param stage: The set representing which characters are currently on stage.
    :returns: The stage and the symidx.
    :raises SplError: If there is an error.
    """

    # first open stage direction
    if symbols[symidx][0] != SYM_OPEN_STAGE_DIRECTION:
        raise SplError('Expected "[" to open a stage direction.')
    
    # then ENTER, EXIT, or EXEUNT
    symidx += 1
    sd_type = symbols[symidx][0]
    if sd_type not in (SYM_STAGE_DIRECTION_ENTER, SYM_STAGE_DIRECTION_EXIT, SYM_STAGE_DIRECTION_EXEUNT):
        raise SplError('Expected "Enter", "Exit", or "Exeunt" in stage direction.')

    symidx += 1

    if sd_type != SYM_STAGE_DIRECTION_EXEUNT:
        # parse the first character
        if symbols[symidx][0] != SYM_CHARACTER:
            raise SplError('Expected character after "Enter" or "Exit".')
        character1 = symbols[symidx][1]
        if character1 not in characters:
            raise SplError('Unknown character in stage direction: ' + character1)
        symidx += 1

    if sd_type == SYM_STAGE_DIRECTION_ENTER:
        # enter can have an optional second character
        if symbols[symidx][0] == SYM_AND:
            symidx += 1
            if symbols[symidx][0] != SYM_CHARACTER:
                raise SplError('Expected second character after "and" in stage direction.')
            character2 = symbols[symidx][1]
            if character2 not in characters:
                raise SplError('Unknown character in stage direction: ' + character2)
            if character2 == character1:
                raise SplError("You can't enter the same character twice in the same stage direction.")
            symidx += 1
        else:
            character2 = None

    # now close stage direction
    if symbols[symidx][0] != SYM_CLOSE_STAGE_DIRECTION:
        raise SplError('Expected "]" to close a stage direction')
    symidx += 1

    # do the things to the stage
    if sd_type == SYM_STAGE_DIRECTION_ENTER:
        if len(stage) == 2 or (character2 is not None and len(stage) > 0):
            raise SplError('Too many characters on stage.')
        if character1 in stage:
            raise SplError(character1 + ' is already on stage.')

        stage.add(character1)
        if character2 is not None:
            stage.add(character2)
    elif sd_type == SYM_STAGE_DIRECTION_EXIT:
        if character1 not in stage:
            raise SplError(character1 + ' is not on stage and cannot exit.')
        stage.remove(character1)
    elif sd_type == SYM_STAGE_DIRECTION_EXEUNT:
        if len(stage) == 0:
            raise SplError('Stage is empty, cannot exeunt.')
        stage.clear()

    return stage, symidx


def validate_line(speaker, spoken_to):
    """
    Raise SplError if a line cannot be spoken right now (i.e. speaker or spoken_to is None).
    :param speaker: The character speaking.
    :param spoken_to: The character being spoken to.
    :raises SplError: if a line cannot be spoken.
    """

    if speaker is None or spoken_to is None:
        raise SplError('A line cannot be spoken because no character is speaking it.')


def parse_character_line_start(symbols, symidx, characters, stage):
    """
    Parse the start of a character's line (e.g. "Juliet:").
    :param symbols: The list of symbols.
    :param symidx: The index into the list of symbols.
    :param characters: The list of characters in the program.
    :param stage: The characters on stage.
    :returns: symidx, speaker, other character (being spoken to).
    :raises SplError: if there is an error.
    """

    # first a character
    if symbols[symidx][0] != SYM_CHARACTER:
        raise SplError('Expected character to start their line.')
    speaker = symbols[symidx][1]
    if speaker not in characters:
        raise SplError('Unknown character ' + speaker)
    if speaker not in stage:
        raise SplError('Character ' + speaker + ' trying to speak while not on stage.')
    if len(stage) != 2:
        raise SplError('Character ' + speaker + ' trying to speak to themselves (or more than 1 person).')
    symidx += 1

    # then a colon
    if symbols[symidx][0] != SYM_COLON:
        raise SplError('Colon expected after character to open their line.')
    symidx += 1

    (spoken_to,) = stage - {speaker}

    return symidx, speaker, spoken_to


def parse_expr_prefix(fmt_str, symbols, symidx, characters, speaker, spoken_to):
    # e.g. "twice", "half"
    symidx, java = parse_expression(symbols, symidx + 1, characters, speaker, spoken_to)
    return symidx, fmt_str.format(java)

def parse_expr_operator(fmt_str, symbols, symidx, characters, speaker, spoken_to):
    # e.g. "sum", "difference"
    symidx, expr1 = parse_expression(symbols, symidx + 1, characters, speaker, spoken_to)
        
    # there must be "and" separating them
    if symbols[symidx][0] != SYM_AND:
        raise SplError('Expected "and" separating two addends of sum.')

    symidx, expr2 = parse_expression(symbols, symidx + 1, characters, speaker, spoken_to)
    return symidx, fmt_str.format(expr1, expr2)


def parse_expression(symbols, symidx, characters, speaker, spoken_to):
    """
    Parse an SPL expression into Java code.
    E.g. "sum of a large green cat and the difference between Romeo and a woman" -> "((2 * (2 * 1)) + (Romeo - 1))"
    :param symbols: The list of symbols.
    :param symidx: The index into the list of symbols.
    :param characters: The list of characters.
    :param speaker: The character speaking.
    :param spoken_to: The character being spoken to.
    :returns: symidx, and the generated Java code representing that expression.
    :raises SplError: if there is an error.
    """

    if symidx >= len(symbols):
        raise SplError('Expression exceeded length of program.')

    if symbols[symidx][0] == SYM_TWICE or symbols[symidx][0] == SYM_ADJECTIVE:
        # twice, adjectives = (2*x)
        return parse_expr_prefix('(2*{})', symbols, symidx, characters, speaker, spoken_to)
    
    elif symbols[symidx][0] == SYM_THRICE:
        # thrice = (3*x)
        return parse_expr_prefix('(3*{})', symbols, symidx, characters, speaker, spoken_to)
    
    elif symbols[symidx][0] == SYM_SQUARE:
        # square = Math.pow(x, 2)
        return parse_expr_prefix('((int) Math.pow({}, 2))', symbols, symidx, characters, speaker, spoken_to)
    
    elif symbols[symidx][0] == SYM_CUBE:
        # cube = Math.pow(x, 3)
        return parse_expr_prefix('((int) Math.pow({}, 3))', symbols, symidx, characters, speaker, spoken_to)
    
    elif symbols[symidx][0] == SYM_SQUARE_ROOT:
        # square root = Math.sqrt(x)
        return parse_expr_prefix('((int) Math.sqrt({}))', symbols, symidx, characters, speaker, spoken_to)

    elif symbols[symidx][0] == SYM_CUBE_ROOT:
        # cube root = Math.cbrt(x)
        return parse_expr_prefix('((int) Math.cbrt({}))', symbols, symidx, characters, speaker, spoken_to)
    
    elif symbols[symidx][0] == SYM_HALF:
        # half = (x/2)
        return parse_expr_prefix('({}/2)', symbols, symidx, characters, speaker, spoken_to)
    
    elif symbols[symidx][0] == SYM_1ST_PERSON_PRONOUN:
        # first person pronouns = the speaker
        return symidx + 1, speaker
    
    elif symbols[symidx][0] == SYM_2ND_PERSON_PRONOUN:
        # second person pronouns = the person being spoken to
        return symidx + 1, spoken_to
    
    elif symbols[symidx][0] == SYM_CHARACTER:
        # characters = that character
        if symbols[symidx][1] not in characters:
            raise SplError(symbols[symidx][1] + ' is not in this program!')
        return symidx + 1, symbols[symidx][1]
    
    elif symbols[symidx][0] == SYM_POSITIVE_NOUN:
        # positive nouns = 1
        return symidx + 1, '1'
    
    elif symbols[symidx][0] == SYM_NEGATIVE_NOUN:
        # negative nouns = -1
        return symidx + 1, '-1'

    elif symbols[symidx][0] == SYM_ZERO:
        # zero: 0
        return symidx + 1, '0'
    
    elif symbols[symidx][0] == SYM_SUM:
        # sum: (x + y)
        return parse_expr_operator('({} + {})', symbols, symidx, characters, speaker, spoken_to)

    elif symbols[symidx][0] == SYM_DIFFERENCE:
        # difference: (x - y)
        return parse_expr_operator('({} - {})', symbols, symidx, characters, speaker, spoken_to)

    elif symbols[symidx][0] == SYM_PRODUCT:
        # product: (x * y)
        return parse_expr_operator('({} * {})', symbols, symidx, characters, speaker, spoken_to)

    elif symbols[symidx][0] == SYM_QUOTIENT:
        # quotient: (x / y)
        return parse_expr_operator('({} / {})', symbols, symidx, characters, speaker, spoken_to)

    elif symbols[symidx][0] == SYM_REMAINDER:
        # remainder of the quotient: (x % y)
        # there must be "quotient" first
        symidx += 1
        if symbols[symidx][0] != SYM_QUOTIENT:
            raise SplError('"Quotient" must appear after "remainder".')
        return parse_expr_operator('({} % {})', symbols, symidx, characters, speaker, spoken_to)

    elif symbols[symidx][0] == SYM_END_PUNCTUATION:
        # ended prematurely: give a more useful error
        raise SplError('Expression ended too soon: did you use an unknown noun/adjective/etc?')

    else:
        # unknown: error
        raise SplError('Unknown symbol in expression: ' + str(symbols[symidx]))


def parse_assignment(symbols, symidx, characters, speaker, spoken_to):
    """
    Parse an assignment - starting with a 2nd person pronoun. E.g. "Thou art as beautiful as a rose".
    :param symbols: The list of symbols.
    :param symidx: The index into the list of symbols.
    :param characters: The list of characters.
    :param speaker: The character speaking.
    :param spoken_to: The character being spoken to (assigned to).
    :returns: symidx, the generated Java code.
    :raises SplError: if there is an error.
    """

    # first: 2nd person pronoun
    if symbols[symidx][0] != SYM_2ND_PERSON_PRONOUN:
        raise SplError('Expected 2nd person pronoun (you, thou, etc.) to start assignment.')
    symidx += 1

    # optional SYM_ASSIGNMENT (art, as, etc.)
    if symbols[symidx][0] == SYM_ASSIGNMENT:
        symidx += 1

    # optional as ... as
    if symbols[symidx][0] == SYM_AS:
        symidx = skip_as(symbols, symidx)

    # expression
    symidx, expr = parse_expression(symbols, symidx, characters, speaker, spoken_to)

    # then end punctuation
    if symbols[symidx][0] != SYM_END_PUNCTUATION:
        raise SplError('End punctuation expected after assignment.')
    symidx += 1

    java = spoken_to + ' = ' + expr + ';'
    return symidx, java


def parse_question(symbols, symidx, characters, speaker, spoken_to, stage):
    """
    Parse a question and the subsequent "if so," and translate into an if statement.
    :param symbols: The list of symbols.
    :param symidx: The index into the list of symbols.
    :param characters: The list of characters.
    :param speaker: The character speaking.
    :param spoken_to: The character being spoken to (assigned to).
    :param stage: The set of characters on stage.
    :returns: symidx, speaker, spoken_to, the generated Java code (this could possibly change
        the speaker/spoken_to if there's a new character line in the middle).
    :raises SplError: if there is an error.
    """

    # a question must start with "is", "art", etc - SYM_ASSIGNMENT
    if symbols[symidx][0] != SYM_ASSIGNMENT:
        raise SplError('"Is", "are", "art", etc. must start a question.')
    symidx += 1

    # expression, then greater than/worse than/as...as, then expression
    symidx, expr1 = parse_expression(symbols, symidx, characters, speaker, spoken_to)

    if symbols[symidx][0] == SYM_AS:
        symidx = skip_as(symbols, symidx)
        op = '=='
    elif symbols[symidx][0] == SYM_GREATER_THAN:
        if symbols[symidx+1][0] == SYM_ADJECTIVE:
            symidx += 1 # skip adjective in case of "more"
        op = '>'
        symidx += 1
    elif symbols[symidx][0] == SYM_LESS_THAN:
        if symbols[symidx+1][0] == SYM_ADJECTIVE:
            symidx += 1 # skip adjective in case of "less"
        op = '<'
        symidx += 1
    else:
        raise SplError('Expression in question must be followed by greater than/less than symbol or as ... as.')

    symidx, expr2 = parse_expression(symbols, symidx, characters, speaker, spoken_to)

    # then a question mark
    if symbols[symidx][0] != SYM_QUESTION_MARK:
        raise SplError('Question must end with question mark.')
    symidx += 1

    # then possibly a new character
    if symbols[symidx][0] == SYM_CHARACTER:
        symidx, speaker, spoken_to = parse_character_line_start(symbols, symidx, characters, stage)

    # then "if so" or "if not" followed by a comma
    if_type = symbols[symidx][0]
    if if_type not in (SYM_IF_SO, SYM_IF_NOT):
        raise SplError('Question must be followed by "if so" or "if not".')
    symidx += 1

    if symbols[symidx][0] != SYM_COMMA:
        raise SplError('"If so" or "if not" must be followed by a comma.')
    symidx += 1

    # maybe invert it depending on "if so" vs "if not"
    fmt_str = 'if ({} {} {})' if if_type == SYM_IF_SO else 'if (!({} {} {}))'
    return symidx, speaker, spoken_to, fmt_str.format(expr1, op, expr2)


def parse_jump(symbols, symidx):
    """
    Parse a "jump" - i.e. let us return to scene [X], we must proceed to act [Y], etc.
    :param symbols: The list of symbols.
    :param symidx: The index into the list of symbols.
    :returns: symidx, SYM_ACT (if jumping to act) or SYM_SCENE (if jumping to scene), act/scene number
    :raises SplError: if there is an error.
    """

    # must start with SYM_JUMP
    if symbols[symidx][0] != SYM_JUMP:
        raise SplError('Jump must start with "let us return", "we shall proceed", etc.')
    symidx += 1

    # next "act" or "scene"
    if symbols[symidx][0] not in (SYM_ACT, SYM_SCENE):
        raise SplError('Jump ("let us return" or similar) must be followed with "act" or "scene".')
    jump_type = symbols[symidx][0]
    symidx += 1

    # then a Roman numeral
    if symbols[symidx][0] != SYM_ROMAN_NUMERAL:
        raise SplError('Act or scene keyword in jump ("let us return", etc.) must be followed by Roman numeral.')
    jump_dest = symbols[symidx][1]
    symidx += 1

    # then end punctuation
    if symbols[symidx][0] != SYM_END_PUNCTUATION:
        raise SplError('Expected end punctuation ("." or "!") to end jump ("let us return", etc.).')
    symidx += 1

    return symidx, jump_type, jump_dest


def translate(spl, java_classname):
    """
    This is the main entry point for actual SPL to Java translation.
    :param spl: The SPL code.
    :param java_classname: The name of the output Java class.
    :returns: The translated Java code.
    :raises SplError: If there is an error in the SPL code.
    """

    tokens = tokenize(spl)
    symbols = symbolize(tokens)

    # filter ignored symbols
    symbols = list(filter(lambda s: s[0] != SYM_IGNORE, symbols))

    if not symbols:
        # the file was empty? or nonsense?
        raise SplError('SPL input was empty or nonsensical.')

    # go past everything up to and including the first SYM_END_PUNCTUATION
    # symidx is the index of the current symbol
    symidx = symbols.index((SYM_END_PUNCTUATION,)) + 1

    # read the list of characters
    characters, symidx = read_characters(symbols, symidx)

    # setup the act and scene counters + stage
    act_counter = 0
    scene_counter = 0
    stage = set()

    # start the Java generation
    java = '''\
// Generated by Ryan Dancy's SPL to Java translator.
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Scanner;

public class %s {
\tprivate static Scanner scanner = new Scanner(System.in);
''' % java_classname

    # add the characters
    for character in characters:
        # there's a stack and a number for each character
        java += '\tprivate static int %s;\n' % character
        java += '\tprivate static Deque<Integer> %s_stk = new ArrayDeque<Integer>();\n' % character

    # add the main method
    java += '\tpublic static void main(String[] args) {\n\t\t'

    speaker = None
    spoken_to = None

    # to make sure we don't jump to a nonexistent act/scene
    acts_scenes_jumped_to = set() # set of (SYM_ACT/SYM_SCENE, act/scene number)

    # to prevent the "unreachable code" error
    last_was_if = False
    need_new_method = False

    # generate the rest of the code
    while symidx != len(symbols):
        symbol = symbols[symidx][0]
        if DEBUG:
            print('Translating: symbol =', symbol, 'symidx =', symidx, 'speaker =', speaker, 'spoken_to =', spoken_to)

        if symbol == SYM_ACT or symbol == SYM_SCENE:
            # starting a new act or scene
            method, symidx, counter = parse_header(symbols, symidx, symbol, act_counter, scene_counter)

            if symbol == SYM_ACT:
                act_counter = counter
                scene_counter = 0 # reset scene counter
            else:
                scene_counter = counter

            # call the new method from the previous one (if it wouldn't cause an error), then start the new one
            if need_new_method:
                java = java[:-1] # remove the last tab
            else:
                java += method + '();\n\t'
            java += '}\n\t'
            java += 'private static void ' + method + '() {\n\t\t'

            need_new_method = False

        elif symbol == SYM_OPEN_STAGE_DIRECTION:
            # stage direction
            stage, symidx = parse_stage_direction(symbols, symidx, characters, stage)
            speaker = spoken_to = None # reset speaker and spoken_to so stage directions can't be in middle of line

        elif symbol == SYM_CHARACTER and symbols[symidx+1][0] == SYM_COLON:
            # character's line start (e.g. "Juliet:")
            if act_counter == 0 or scene_counter == 0:
                raise SplError('A character cannot speak outside of an act and scene.')
            symidx, speaker, spoken_to = parse_character_line_start(symbols, symidx, characters, stage)

        elif symbol == SYM_2ND_PERSON_PRONOUN:
            # assigning to the spoken_to character
            validate_line(speaker, spoken_to)
            symidx, assignment = parse_assignment(symbols, symidx, characters, speaker, spoken_to)
            java += assignment + '\n\t\t'

        elif symbol == SYM_ASSIGNMENT:
            # question
            validate_line(speaker, spoken_to)
            symidx, speaker, spoken_to, if_statement = parse_question(symbols, symidx, characters, speaker, spoken_to, stage)
            java += if_statement + ' '

        elif symbol == SYM_JUMP:
            # jump to another scene - call the method then return
            validate_line(speaker, spoken_to)
            symidx, act_or_scene, number = parse_jump(symbols, symidx)
            acts_scenes_jumped_to.add((act_or_scene, number))
            
            # in a block so that it can be used with if statements/questions
            java += '{ %s%d(); return; }\n\t\t' % ('act' if act_or_scene == SYM_ACT else 'act%dscene' % act_counter, number)

            if not last_was_if:
                need_new_method = True # it's a definite return

        elif symbol == SYM_PUSH_TO_STACK:
            # push to spoken_to's stack ("remember")
            validate_line(speaker, spoken_to)
            symidx = skip_till_end_punct(symbols, symidx)
            java += '{0}_stk.push({0});\n\t\t'.format(spoken_to)

        elif symbol == SYM_POP_FROM_STACK:
            # pop from spoken_to's stack ("recall")
            validate_line(speaker, spoken_to)
            symidx = skip_till_end_punct(symbols, symidx)
            java += '{0} = {0}_stk.pop();\n\t\t'.format(spoken_to)

        elif symbol == SYM_INPUT_NUMBER:
            # input a number into spoken_to ("listen to your/thy heart")
            validate_line(speaker, spoken_to)
            symidx = next_is(symbols, symidx + 1, SYM_END_PUNCTUATION, 'Expected end punctuation after "listen to your/thy heart".')
            java += '{} = scanner.nextInt();\n\t\t'.format(spoken_to)

        elif symbol == SYM_INPUT_CHARACTER:
            # input a character into spoken_to ("open your/thy mind")
            validate_line(speaker, spoken_to)
            symidx = next_is(symbols, symidx + 1, SYM_END_PUNCTUATION, 'Expected end punctuation after "open your/thy mind".')
            java += '''try {{
\t\t\t{0} = scanner.findInLine(".").charAt(0);
\t\t}} catch (NullPointerException e) {{
\t\t\t{0} = -1;
\t\t}}
\t\t'''.format(spoken_to)

        elif symbol == SYM_OUTPUT_NUMBER:
            # output a number from spoken_to ("open your/thy heart")
            validate_line(speaker, spoken_to)
            symidx = next_is(symbols, symidx + 1, SYM_END_PUNCTUATION, 'Expected end punctuation after "open your/thy heart".')
            java += 'System.out.print({});\n\t\t'.format(spoken_to)

        elif symbol == SYM_OUTPUT_CHARACTER:
            # output a character from spoken_to ("speak your/thy mind")
            validate_line(speaker, spoken_to)
            symidx = next_is(symbols, symidx + 1, SYM_END_PUNCTUATION, 'Expected end punctuation after "speak your/thy mind".')
            java += 'System.out.print((char) {});\n\t\t'.format(spoken_to)

        elif symbol == SYM_END_PUNCTUATION:
            # ignore double punctuation like !!
            symidx += 1 # just skip it

        else:
            # unknown symbol
            raise SplError('Bad symbol at start of line; symbol=' + str(symbol))

        last_was_if = (symbol == SYM_ASSIGNMENT)
        if need_new_method and symbol not in (SYM_JUMP, SYM_END_PUNCTUATION):
            # there was non-act/scene code after an unguarded jump
            raise SplError('A jump unguarded by a question must be the last statement in its act or scene.')

    # validate the acts and scenes jumped to
    for act_or_scene, num in acts_scenes_jumped_to:
        if act_or_scene == SYM_ACT and num > act_counter:
            raise SplError('Jump to nonexistent act ' + num)
        if act_or_scene == SYM_SCENE and num > scene_counter:
            raise SplError('Jump to nonexistent scene ' + num)

    return java[:-1] + '}\n}\n' # remove last "\t"
