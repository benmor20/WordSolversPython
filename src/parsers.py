from word_objects import *
from typing import *


_BRACKET_MATCHES = {'[': ']',
                    '{': '}',
                    '(': ')'}


def parse_blank_space(string: str) -> Optional[BlankSpace]:
    if string is None or len(string) == 0:
        return None
    unknown = string.lower()
    if len(unknown) == 1:
        if unknown == '_':
            return BlankSpace(False)
        if 'a' <= unknown <= 'z':
            return BlankSpace(False, chars=unknown)
        _raise_parse_error('BlankSpace', string, 'Single-character BlankSpace must be a letter or underscore', 0)

    bracket = unknown[0]
    if bracket not in '[{(':
        _raise_parse_error('BlankSpace', string, 'Multiple character BlankSpace must start with [, {, or (', 0)
    end_bracket = unknown[-1]
    if end_bracket != _BRACKET_MATCHES[bracket]:
        _raise_parse_error('BlankSpace', string, 'Last character must match the starting bracket', len(unknown) - 1)

    unknown = unknown[1:-1]
    if len(unknown) == 0:
        _raise_parse_error('BlankSpace', string, 'Missing characters inside bracket', 1)
    index = 0
    is_filter = bracket != '['
    minlen = 1
    maxlen = -1 if is_filter else 1  # Default bounds depend on whether it is a filter

    c = unknown[index]
    if '0' <= c <= '9':  # If number, has bounds - set min
        index = unknown.find(',')
        if index == -1:
            _raise_parse_error('BlankSpace', string, 'Missing comma in length bounds', len(unknown) + 1)
        try:
            minlen = int(unknown[:index])
        except ValueError:
            _raise_parse_error('BlankSpace', string, f'Could not parse a minimum bound from {unknown[:index]}',
                               index + 1)
        c = unknown[index]
    if c == ',':  # Will arrive here if no min or if above if was entered
        if index == 0:  # No min (did not enter previous if)
            minlen = 0
        index += 1
        if index < len(unknown):
            c = unknown[index]
            if '0' <= c <= '9':
                maxlen = 0
                while '0' <= c <= '9':
                    maxlen *= 10
                    maxlen += int(c)
                    index += 1
                    if index == len(unknown):
                        break
                    c = unknown[index]
            else:  # No max
                maxlen = -1
        else:  # No max and no characters
            maxlen = -1
    if -1 < maxlen < minlen:
        _raise_parse_error('BlankSpace', string, f'Lower bound ({minlen}) cannot be more than upper bound ({maxlen})',
                           index + 1)

    if index < len(unknown):  # Character limits given
        negated = False
        if unknown[index] in '^!':
            negated = True
            index += 1
        if index < len(unknown):
            res = BlankSpace(True, negated, minlen, maxlen)
            c = unknown[index]
            if 'a' <= c <= 'z':
                while 'a' <= c <= 'z':
                    res.append(c)
                    index += 1
                    if index == len(unknown):
                        return res
                    c = unknown[index]
            _raise_parse_error('BlankSpace', string, f'Unexpected character: {c}', index + 1)
        else:  # ^ ends the brackets
            return BlankSpace(True, negated, minlen, maxlen)
    else:  # Only bounds given
        return BlankSpace(True, False, minlen, maxlen, all_character_set())


def parse_unknown_word(string: str) -> Optional[UnknownWord]:
    if string is None or len(string) == 0:
        return None
    unknown = string.lower()
    spaces = []
    filter = None
    hard_filter = False
    index = 0
    while index < len(unknown):
        c = unknown[index]
        if c == '_' or 'a' <= c <= 'z':
            spaces.append(parse_blank_space(c))
        elif c == '[' or c == '{' or c == '(':
            end_bracket = _BRACKET_MATCHES[c]
            end_index = unknown[index:].find(end_bracket) + index
            space = parse_blank_space(unknown[index:end_index + 1])
            index = end_index
            if c == '[':
                spaces.append(space)
            else:
                filter = space
                hard_filter = c == '{'
                if index != len(unknown) - 1:
                    _raise_parse_error('UnknownWord', string, 'Filter must be at the end of the word', index)
        else:
            _raise_parse_error('UnknownWord', string, f'Unexpected character: {c}', index)
        index += 1
    return UnknownWord(spaces, filter, hard_filter)


def _raise_parse_error(class_name: str, unknown: str, msg: str, index: int):
    raise ValueError(f'Could not parse {class_name} from {unknown}: {msg} (index {index})')
