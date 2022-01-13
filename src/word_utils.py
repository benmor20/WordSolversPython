from typing import *
from word_objects import *
from collections import defaultdict


_DICTIONARY: List[str] = []
_DICT_TRIE: Optional[DictionaryNode] = None
_FREQUENCIES: Dict[str, int] = defaultdict()
_RANKINGS: Dict[str, int] = defaultdict()
_WORDS_RANKED: List[str] = []


def _read_dict(dict_path: str, freq_path: str):
    """
    Populates the data structures above from the given files

    :param dict_path: The path to the dictionary file (a list of words)
    :param freq_path: The path to the frequency file (a list of words and their frequencies, tab separated)
    """
    global _DICTIONARY
    global _DICT_TRIE
    global _FREQUENCIES
    global _RANKINGS
    global _WORDS_RANKED
    with open(freq_path, 'r') as freq_file:
        for index, line in enumerate(freq_file.readlines()):
            splt = line.lower().split('\t')
            word, freq = splt[0], int(splt[1])
            _FREQUENCIES[word] = freq
            _RANKINGS[word] = index + 1
            _WORDS_RANKED.append(word)
    with open(dict_path, 'r') as dct_file:
        _DICTIONARY = [w.lower() for w in dct_file.readlines()]
    _DICT_TRIE = create_dict_trie(_DICTIONARY)


def read_dict():
    """
    Reads the dictionaries from their default locations
    """
    _read_dict('data/words.txt', 'data/frequencies.txt')


def is_word(word: str) -> bool:
    """
    Finds whether a given is a word

    :param word: word to test
    :return: whether the word is in the dictionary
    """
    if _DICT_TRIE is None:
        read_dict()
    return _DICT_TRIE.has_child(clean_word(word))


def is_phrase(phrase: str) -> bool:
    """
    Finds whether a phrase consists of entirely real words

    :param phrase: the phrase to test
    :return: whether every word in the phrase is in the dictionary
    """
    return all(map(is_word, phrase.split(' ')))


def get_frequency(word: str) -> int:
    """
    Finds the frequency of the word, or 0 if it does not exist.

    Words that exist but are not in the frequency list are assumed to have a frequency of 1

    :param word: The word to look up
    :return: the frequency of the given word
    """
    if _FREQUENCIES is None:
        read_dict()
    freq = _FREQUENCIES[clean_word(word)]
    if freq is None:
        return 1 if is_word(word) else 0
    return freq


def get_ranking(word: str) -> int:
    """
    Finds the ranking of the word, if it exists.

    If the word is not in the rankings, it will assume:
        -The rank is one after the last ranked word if the word exists
        -The rank is the number of ranked words times 100 if the word does not exist

    :param word: the word to lookup
    :return: the ranking of the word
    """
    if _RANKINGS is None:
        read_dict()
    rank = _RANKINGS[clean_word(word)]
    if rank is None:
        return len(_RANKINGS) + 1 if is_word(word) else len(_RANKINGS) * 100
    return rank


def get_dict() -> List[str]:
    """
    :return: a list of all words in the dictionary
    """
    if _DICTIONARY is None:
        read_dict()
    return _DICTIONARY.copy()


def get_dict_trie() -> DictionaryNode:
    """
    :returns: A DictionaryNode representing the root of a Trie containing all words in the dictionary
    """
    if _DICT_TRIE is None:
        read_dict()
    return _DICT_TRIE


def get_ordered_words() -> List[str]:
    """
    :returns: a list of words sorted by frequency
    """
    if _WORDS_RANKED is None:
        read_dict()
    return _WORDS_RANKED.copy()


def get_word_from_ranking(rank: int) -> str:
    """
    Finds the word with the given rank

    :param rank: the rank to look up
    :return: the word whose rank matches the given
    """
    if _WORDS_RANKED is None:
        read_dict()
    return _WORDS_RANKED[rank]


def create_dict_trie(words: List[str]) -> DictionaryNode:
    """
    Creates a Trie from a list of words

    :param words: a list of words, the basis of the trie
    :return: a DictionaryNode, the root of the trie containing all words in words
    """
    root = DictionaryNode()
    for word in words:
        current = root
        word = clean_word(word)
        for index, c in enumerate(word[:-1]):
            if current.has_child(c):
                current = current.get_child(c)
            else:
                current = current.make_child(c)
        last = word[-1]
        if current.has_child(last):
            current.get_child(last).is_word = True
        else:
            current.make_child(last, True)
    return root


def create_tree_from_most_common(num_words: int):
    """
    Created a trie from only the most common n words

    :param num_words: The number of words to include in the trie
    :return: a trie formed from the most common words
    """
    if _WORDS_RANKED is None:
        read_dict()
    return create_dict_trie(_WORDS_RANKED[:num_words])


def clean_word(word: str) -> str:
    """
    Cleans a given word to match the format of the data structures

    Specifically, this removes any non-alphabetic characters and converts the word to lowercase

    :param word: the word to clean
    :return: the cleaned word
    """
    return ''.join(c for c in word.lower() if 'a' <= c <= 'z')
