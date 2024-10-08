"""
    : Helper function for updating algorithm values in the
    : JSON file

    Returns:
        JSON: Updated JSON file based on algorithm values when if
        needing updated
"""

from typing import Any, Tuple, Dict
from config import LEVEL_CONSTANTS


def update_values(
        level_key: Tuple,
        algo_vals: Dict):
    """
        : Function to check if the values that the main algorithm
        : needs to do calculations were needing to be updated. If
        : so, then check if value it is non-falsy and not a matching
        : value.

    Args:
        level_key (Tuple): Values used to search in LEVEL_CONSTANTS
        algo_vals (Dict): Dictionary from create sports
    """

    params = [
        'k_value',
        'home_advantage',
        'average_game_score',
        'game_set_len'
    ]
    for param in params:
        replacement_value = algo_vals.get(param)
        lvl_check = LEVEL_CONSTANTS[level_key][param]

        if replacement_value and replacement_value != lvl_check:
            LEVEL_CONSTANTS[level_key][param] = replacement_value
