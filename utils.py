from itertools import cycle
from random import choice


def get_random_string(length) -> str:
    letters = ('qwrtpsdfghjklzxcvbnm', 'eyuioa')
    cycle_ = zip(cycle(letters), range(length))
    return ''.join(choice(letter) for letter, _ in cycle_)


def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i+n]