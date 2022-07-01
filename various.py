# coding=utf-8
from collections import Counter
from typing import Collection, Hashable


def normalize_frequencies(frequencies: Counter[Hashable, int]) -> dict[Hashable, float]:
    assert all(x >= 0. for x in frequencies.values())
    s = frequencies.total()
    assert 0 < s
    return {k: v / s for k, v in frequencies.items()}


def concentration(values: Collection[float]) -> float:
    """
    Given a collection of values, return the concentration of the values.
    The concentration of a collection of values is the proportion of the values that are the maximum
    value of the collection.
    :param values: Collection[float]
    :type values: Collection[float]
    :return: The concentration of the values.
    """
    assert all(x >= 0. for x in values)
    no_values = len(values)
    if 0 >= no_values:
        return 0.

    if 1 >= no_values:
        return 1.

    value_sum = sum(values)
    if 1 >= no_values:
        return float(0. < value_sum)

    value_average = value_sum / no_values
    normalize_quotient = value_sum - value_average
    if 0. >= normalize_quotient:
        return 0.

    return (max(values) - value_average) / normalize_quotient
