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
    NULL = -1


def one_higher(value: DiceValue):
    if value == DiceValue.SIX or value == DiceValue.NULL:
        return DiceValue.NULL
    return DiceValue(value.value+1)


def x_higher(x: int, value: DiceValue):
    if value == DiceValue.NULL:
        return DiceValue.NULL
    if value.value+x > 6:
        return DiceValue.NULL
    return DiceValue(value.value+x)


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

    NULL = -1


def to_value(face: DiceFace) -> DiceValue:
    if face.value <= 6:
        return DiceValue(face.value)
    if face == DiceFace.STAR_ONE:
        return DiceValue.ONE
    return DiceValue.NULL


class DiceType(Enum):
    STANDARD = 0
    IMMEDIATE = 1
    SERF = 2
    NOBLE = 3
    ARTISAN = 4
    INTRIGUE = 5
    VOYAGE = 6
    DECREE = 7


class ScarabType(Enum):
    REROLL = 0
    PIPUP = 1


class TurnStep(Enum):
    TURN_START = 0
    ROLLS = 1
    CLAIM = 2
    LOCK = 3

    NONE = -1
