from enum import Enum


class RowMode(Enum):
    A = 0
    B = 1


class TileType(Enum):
    YELLOW = 0
    BLUE = 1
    RED = 2


class DiceValue(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6


class DiceFace(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6

    STAR_ONE = 7
    TWO_STAR = 8
    STAR = 9
    REROLL = 10
    ADD_TWO = 11
    BLANK = 12
    STAR_DECREE = 13
