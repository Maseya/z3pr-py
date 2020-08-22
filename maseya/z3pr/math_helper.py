from itertools import chain, combinations
from typing import Iterable


def clamp(value, min_bound, max_bound, less=lambda x, y: x < y):
    if less(value, min_bound):
        return min_bound
    if less(max_bound, value):
        return max_bound
    return value


def powerset(iterable: Iterable) -> Iterable[Iterable]:
    """Generate all subsets of a set"""
    items = list(iterable)
    return chain.from_iterable(combinations(items, r) for r in range(len(items) + 1))
