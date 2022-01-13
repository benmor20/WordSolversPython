from typing import *
from string import ascii_lowercase
from copy import deepcopy
from collections import defaultdict


def all_character_set():
    """
    :return: A set of the lowercase letters. Written as a function so result can be modified
    """
    return set(ascii_lowercase)


class DictionaryNode:
    """
    One node of a Trie for words, able to traverse both up and down.

    Attributes:
        is_word: bool. Whether this node is a full word or only part of one. Note that this is not the same as leaf
            nodes. For instance, "the" is a word but it also has many children.
        _parent: Optional, DictionaryNode. This node's parent, or None if this node is the root.
        _parent_path: Optional, char. The character connecting this node to it's parent, if it exists.
        _child_map: Optional, Dict char -> DictionaryNode. Stores this node's children and the path to each.
    """
    def __init__(self, parent: Optional['DictionaryNode'] = None, parent_path: Optional[str] = None,
                 is_word: bool = False):
        assert parent_path is None or len(parent_path) == 1
        assert (parent is None) == (parent_path is None)
        self._parent = parent
        self._parent_path = parent_path
        self.is_word = is_word
        self._child_map = defaultdict()

    @property
    def is_root(self) -> bool:
        """
        :return: True iff this node is the root node (the parent is None)
        """
        return self._parent is None

    @property
    def parent(self) -> Optional['DictionaryNode']:
        """
        :return: The parent node
        """
        return self._parent

    @property
    def root(self) -> 'DictionaryNode':
        """
        :return: The root of this Trie. Note that this runtime is linear with depth (~log with trie size)
        """
        return self if self.is_root else self.parent.is_root

    @property
    def children(self) -> Dict[str, 'DictionaryNode']:
        """
        :return: The children of this node.
        """
        return self._child_map

    @property
    def depth(self) -> int:
        """
        :return: The depth of this node. Note that this runtime is linear with depth (~log with trie size)
        """
        return 0 if self.is_root else self.parent.depth + 1

    @property
    def max_layers_below(self) -> int:
        """
        :return: The maximum number of layers below this node. Note that this runtime is linear with depth
            (~log with trie size)
        """
        max_layers = -1
        for c in self.children.values():
            max_layers = max(max_layers, c.max_layers_below)
        return max_layers + 1

    def make_child(self, path: str, is_word: bool = False) -> 'DictionaryNode':
        """
        Makes a child with the specified path, adds it to the trie and returns it

        :param path: The character connecting this node to the new one
        :param is_word: Whether the new child is a word. Defaults to False.
        :return: The child
        """
        assert len(path) == 1
        self.children[path] = DictionaryNode(self, path, is_word)
        return self.children[path]

    def add_child(self, path: str, child: 'DictionaryNode') -> 'DictionaryNode':
        """
        Adds the child to the trie along the specified path.

        :param path: The character connecting this node to the child
        :param child: The child to connect
        :return: The child
        """
        self.children[path] = child
        child._parent = self
        child._parent_path = path
        return child

    def has_child(self, path: str):
        """
        Finds if this node has a descendant along the specified path (char or str)

        Example:
            If n represents "the", then n.has_child("saurus") returns whether "thesaurus" is in the trie

        :param path: The path to check for
        :return: True iff there is a node following the string specified by path.
        """
        if len(path) == 1:
            return path in self.children
        if path[0] in self.children:
            return self[path[0]].has_child(path[1:])
        return False

    def get_child(self, path: str) -> Optional['DictionaryNode']:
        """
        Finds and returns the child specified by the path, if it exists

        :param path: The path to the child to look for
        :return: the child at the path, or None if it does not exist
        """
        if len(path) == 0:
            return self
        if self.has_child(path[0]):
            return self.children[path[0]].get_child(path[1:])
        return None

    def get_possible_children(self, space: 'BlankSpace') -> Iterator['DictionaryNode']:
        """
        Finds all possible children that could be specified by the given BlankSpace

        :param space: The pattern to match to
        :return: an iterator through all possible children of this node specified by space
        """
        if space.min_blanks == 0:
            yield self
        if space.max_blanks == 0:
            return
        for c in space.possible_characters:
            if not self.has_child(c):
                continue
            yield from self[c].get_possible_children(space.clone_minus())

    def all_words(self):
        """
        :return: an iterator of all words that are below this node in the trie
        """
        if self.is_word:
            yield str(self)
        for c in self.children.values():
            yield from c.all_words()

    def __getitem__(self, item: str) -> Optional['DictionaryNode']:
        if len(item) == 1:
            return self.children.get(item)
        if self.has_child(item[0]):
            return self.children[item[0]][item[1:]]
        return None

    def __repr__(self):
        return '' if self.is_root else f'{self.parent}{self._parent_path}'


class BlankSpace:
    """
    Represents a singular unknown letter or set of letters. One element of an UnknownWord. Can represent:
        - A single letter ("a")
        - Any single letter ("_")
        - A set of letters ("[abc]" matches a, b, or c)
        - A set of any single letter except some ("[^abc]" matches d, e, f, etc. but not a, b, or c)
        - Any pattern above, repeated some number of times ("[3,3abc]" matches aaa, bbb, abc, cab, caa, etc)
        - Any pattern above, repeated a variable number of times ("[1,3abc]" matches a, b, c, aa, ab, abc, cab, etc)
        - Any pattern above, repeated any number of times
            ("[3,abc]" matches any permutation of abc more than 3 letters long,
             "[,3abc]" matches any permutation of abc up to 3 letters long,
             "[,abc]" matches any permutation of abc of any length)

    Attributes:
        bracketed: Whether this space is bracketed ("[abc]" vs "a" or "_"). Useful for __repr__ and filtering (see UnknownWord)
        _negated: Whether to add or remove letters from possible_characters in the append function
        possible_characters: A set of characters this space could represent
        min_blanks: The least amount of letters this space can use. Default 1.
        max_blanks: the most amount of letters this space can use. Default 1.
    """
    def __init__(self, bracketed: bool, negated: bool = False, min_blanks: int = 1, max_blanks: int = 1,
                 chars: Union[str, Collection[str]] = ''):
        self.possible_characters = all_character_set() if (not bracketed and chars == '') or negated else set()
        self.min_blanks = min_blanks
        self.max_blanks = max_blanks
        self._negated = negated
        self.bracketed = bracketed
        self.append(chars if isinstance(chars, str) else ''.join(chars))

    @property
    def negated(self) -> bool:
        """
        :return: If this BlankSpace is negated (if appending characters will remove them from possible_characters)
        """
        return self._negated

    @property
    def is_empty(self) -> bool:
        """
        :return: If this BlankSpace cannot represent anything
        """
        return self.max_blanks == 0

    @property
    def is_singular(self) -> bool:
        """
        :return: If this blank space can only represent one character
        """
        return self.min_blanks == 1 and self.max_blanks == 1

    @property
    def is_all_chars(self) -> bool:
        """
        :return: If this blank space can represent any character (regardless of number of blanks)
        """
        return self.possible_characters == all_character_set()

    @property
    def is_determinant(self) -> bool:
        """
        :return: Whether this blank space can represent more than one thing
        """
        return len(self.possible_characters) == 1 and self.min_blanks == self.max_blanks

    def append(self, chars: str):
        """
        Given a list of additions in the bracket (i.e. the "abc" in "[abc]" or "[^abc]"), adds or removes the characters
            from possible_characters, depending on the value of negated

        :param chars: The letters to add or remove
        """
        if self.negated:
            self.remove(chars)
        else:
            self.add(chars)

    def remove(self, chars: str):
        """
        Removes the list of characters from the possibilities

        :param chars: the list of characters to remove=
        """
        s = set(chars)
        self.possible_characters -= s

    def add(self, chars: str):
        """
        Adds the list of characters to the possibilities

        :param chars:
        """
        s = set(chars)
        self.possible_characters.update(s)

    def apply_filter(self, filter_chars: Union[str, Collection[str]], hard: bool = False):
        """
        Applies a filter to this BlankSpace. See README for an explanation of filters.

        :param filter_chars: The characters to filter
        :param hard: Whether to apply a hard filter
        """
        filter_chars = set(filter_chars if isinstance(filter_chars, str) else ''.join(filter_chars))
        if (hard and (self.bracketed or len(self.possible_characters) > 1))\
                or (not hard and not self.bracketed and len(self.possible_characters) > 1):
            self.remove(''.join(all_character_set() - filter_chars))

    def with_filter(self, filter_chars: Union[str, Collection[str]], hard: bool = False) -> 'BlankSpace':
        """
        Creates a BlankSpace representative of this BlankSpace with the given filter.

        :param filter_chars: The characters to filter
        :param hard: Whether to apply a hard filter
        :return: A new BlankSpace that is self with the applied filter.
        """
        clone = deepcopy(self)
        clone.apply_filter(filter_chars, hard)
        return clone

    def clone_minus(self, sub_min: int = 1, sub_max: Optional[int] = None) -> 'BlankSpace':
        """
        A clone of self, subtracting a certain number of possible spaces.

        Examples:
            [3,5].clone_minus(1, 1) -> [2,4]
            [5,10].clone_minus(3, 6) -> [,8]

        :param sub_min: The minimum number of blanks to remove. Defaults to 1
        :param sub_max: The maximum number of blanks to remove, or None to set this equal to sub_min. Defaults to None.
        :return: A clone of self without the specified number of blanks
        """
        if self.is_empty:
            raise ValueError('Cannot create a new BlankSpace with less spaces than none')
        if sub_max is None:
            sub_max = sub_min
        new_min = max(0, self.min_blanks - sub_max)
        new_max = -1 if self.max_blanks == -1 else self.max_blanks - sub_min
        clone = BlankSpace(self.bracketed, self.negated, new_min, new_max)
        clone.possible_characters = set(self.possible_characters)
        return clone

    def __repr__(self) -> str:
        if not self.bracketed and not self.negated:
            if len(self.possible_characters) == 1:
                return list(self.possible_characters)[0]
            elif len(self.possible_characters) == 26:
                return '_'
        if self.negated:
            char_str = f'^{"".join(all_character_set() - self.possible_characters)}'
        elif not self.is_all_chars:
            char_str = ''.join(sorted(self.possible_characters))
        else:
            char_str = ascii_lowercase
        if self.min_blanks == self.max_blanks == 1:
            return f'[{char_str}]'
        min_str = '' if self.min_blanks == 0 else str(self.min_blanks)
        max_str = '' if self.max_blanks == -1 else str(self.max_blanks)
        return f'[{min_str},{max_str}{"" if char_str == ascii_lowercase else char_str}]'


class UnknownWord:
    """
    Represents a singular unknown word - a list of BlankSpaces with a possible filter.
    See README for an explanation of filters.

    Attributes:
        spaces: A list of BlankSpaces - the spaces of this word in order
        filter: A BlankSpace that represents the letter and length filter over this word, or None if there is no filter
        hard_filter: Whether the filter (if it exists) is a hard filter.
    """
    def __init__(self, spaces: List[BlankSpace], filter: Optional[Union[str, Collection[str], BlankSpace]] = None,
                 hard_filter: bool = False):
        self.spaces = [deepcopy(s) for s in spaces]
        self.filter = None if filter is None else deepcopy(filter)
        if self.filter is not None and not self.filter.bracketed:
            raise ValueError('A filter must be bracketed')
        self.hard_filter = hard_filter

    @property
    def has_filter(self) -> bool:
        """
        :return: whether this word has a filter
        """
        return self.filter is not None

    @property
    def is_determinant(self) -> bool:
        """
        :return: whether this word can only represent one thing
        """
        return all([s.is_determinant for s in self.spaces])

    @property
    def _calc_length_bounds(self) -> Tuple[int, int]:
        """
        :return: A tuple of the calculated min and max length (i.e. ignoring the filter)
        """
        calc_min, calc_max = 0, 0
        for space in self.spaces:
            calc_min += space.min_blanks
            calc_max = -1 if calc_max == -1 or space.max_blanks == -1 else calc_max + space.max_blanks
        return calc_min, calc_max

    @property
    def min_letters(self) -> int:
        """
        :return: The minimum number of letters this word can have
        """
        calc_min = self._calc_length_bounds[0]
        if not self.has_filter:
            return calc_min
        return max(calc_min, self.filter.min_blanks)

    @property
    def max_letters(self) -> int:
        """
        :return: The maximum number of letters this word can have
        """
        calc_max = self._calc_length_bounds[1]
        if not self.has_filter:
            return calc_max
        if calc_max == -1 or self.filter.max_blanks == -1:
            return max(calc_max, self.filter.max_blanks)
        return min(calc_max, self.filter.max_blanks)

    @property
    def is_possible(self) -> bool:
        """
        Calculates whether this word is possible.

        A word is not possible if the calculated bounds of the word (i.e. ignoring the filter) are completely outside
            the bounds specified by the filter. For example "ab_{10,20}" is not possible.

        :return: Whether this word is possible
        """
        calc_min, calc_max = self._calc_length_bounds
        return not self.has_filter or self.filter.min_blanks <= calc_min <= self.filter.max_blanks\
               or self.filter.min_blanks <= calc_max <= self.filter.max_blanks

    def get_effective_spaces(self) -> List[BlankSpace]:
        """
        :return: The list of spaces, with the filter applied if it exists
        """
        if not self.has_filter:
            return self.spaces
        return [s.with_filter(self.filter.possible_characters, self.hard_filter) for s in self.spaces]

    def get_effective_space(self, index: int) -> BlankSpace:
        """
        :param index: The index of the space to return
        :return: The specified BlankSpace, filtered
        """
        if not self.has_filter:
            return self[index]
        return self[index].with_filter(self.filter.possible_characters, self.hard_filter)

    def without_space(self, index: int) -> 'UnknownWord':
        """
        :param index: The space to cut
        :return: A new UnknownWord without the specified space.
        """
        cut = self[index]
        new_filter = self.filter.clone_minus(cut.min_blanks, cut.max_blanks) if self.has_filter else None
        return UnknownWord(self.spaces[:index] + self.spaces[index + 1:], new_filter, self.hard_filter)

    def without_first_letter(self) -> Optional['UnknownWord']:
        """
        Creates a new UnknownWord without the first letter.

        Note that this is different from an UnknownWord without the first space, as a space can represent many letters.

        :return: A copy of this UnknownWord if the first letter was not there
        """
        calc_min, calc_max = self._calc_length_bounds
        if calc_max == 0:
            return None
        elif calc_max == 1:
            return UnknownWord([], self.filter.clone_minus() if self.has_filter else None, self.hard_filter)
        first = self[0]
        skip_first = [deepcopy(s) for s in self[1:]]
        filter_minus_one = self.filter.clone_minus() if self.has_filter else None
        if first.max_blanks == 0:
            return UnknownWord(skip_first, self.filter, self.hard_filter)
        elif first.max_blanks == 1:
            return UnknownWord(skip_first, filter_minus_one, self.hard_filter)
        else:
            return UnknownWord([first.clone_minus()] + skip_first, filter_minus_one, self.hard_filter)

    def __getitem__(self, item):
        return self.spaces[item]

    def __len__(self) -> int:
        return len(self.spaces)

    def __repr__(self) -> str:
        res = ''.join(str(s) for s in self)
        if not self.has_filter:
            return res
        filter_str = str(self.filter)
        open_bracket = '{' if self.hard_filter else '('
        close_bracket = '}' if self.hard_filter else ')'
        return f'{res}{open_bracket}{filter_str[1:-1]}{close_bracket}'

