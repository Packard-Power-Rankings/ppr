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
        algo_vals: Dict) -> Any:
    """
        : Updates Algorithm values if any are passed through
        : and uses defaults that are set in LEVEL_CONSTANTS. Also
        : it will update values in LEVEL_CONSTANTS as well.

    Args:
        level_key (Tuple): Values used to search in LEVEL_CONSTANTS
        sport_json_doc (Any): JSON file to be updated
        algo_vals (Dict): Keyword dictionary from create sports

    Returns:
        JSON: Returns an updated JSON file with the updated algorithm
        values stored appropriately.
    """

    params = [
        'k_value',
        'home_advantage',
        'average_game_score',
        'game_set_len'
    ]
    for param in params:
        new_value = algo_vals.get(param, LEVEL_CONSTANTS[level_key][param])

        if param in algo_vals:
            LEVEL_CONSTANTS[level_key][param] = new_value
