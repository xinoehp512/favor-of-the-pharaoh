from collections.abc import Callable
from enums import *

ConstraintFunc = Callable[[list[DiceValue]], bool]


def constraint_intersection(*args: ConstraintFunc) -> ConstraintFunc:
    def intersection(dice: list[DiceValue]):
        return all(constraint(dice) for constraint in args)
    return intersection


def constraint_union(*args: ConstraintFunc) -> ConstraintFunc:
    def union(dice: list[DiceValue]):
        return any(constraint(dice) for constraint in args)
    return union


def get_freq_dist(dice: list[DiceValue]):
    freq_dist = {i: dice.count(i) for i in set(dice)}
    # if DiceFace.STAR_ONE in freq_dist:
    #     freq_dist[DiceFace.ONE] = freq_dist.get(DiceFace.ONE, 0)+freq_dist[DiceFace.STAR_ONE]
    return freq_dist


def x_of_a_kind(x: int) -> ConstraintFunc:
    def func(dice: list[DiceValue]) -> bool:
        face_freq = get_freq_dist(dice)
        for value in face_freq.values():
            if value >= x:
                return True
        return False
    return func


def x_y_z_of_a_kind(xyz: list[int]) -> ConstraintFunc:
    xyz = sorted(xyz, reverse=True)

    def func(dice: list[DiceValue]) -> bool:
        face_freq = get_freq_dist(dice)
        set_values = sorted(face_freq.values(), reverse=True)
        for requirement_value in xyz:
            if set_values[0] < requirement_value:
                return False
            set_values[0] -= requirement_value
            set_values.sort(reverse=True)
        return True
    return func


def contains(dice_list: list[DiceValue]) -> ConstraintFunc:
    freq_dist = get_freq_dist(dice_list)

    def func(dice: list[DiceValue]) -> bool:
        face_freq = get_freq_dist(dice)
        return all(value <= face_freq.get(key, 0) for key, value in freq_dist.items())
    return func


def all_condition(condition: Callable[[DiceValue], bool]):
    def func(dice: list[DiceValue]) -> bool:
        return all(condition(face) for face in dice)
    return func


def greater_than_equal_to_value(value: int) -> ConstraintFunc:
    def func(dice: list[DiceValue]) -> bool:
        return sum(face.value for face in dice) >= value
    return func


pair = x_of_a_kind(2)
three_of_a_kind = x_of_a_kind(3)
four_of_a_kind = x_of_a_kind(4)
five_of_a_kind = x_of_a_kind(5)
six_of_a_kind = x_of_a_kind(6)
seven_of_a_kind = x_of_a_kind(7)

two_pairs = x_y_z_of_a_kind([2, 2])
three_pairs = x_y_z_of_a_kind([2, 2, 2])
pair_and_three_of_a_kind = x_y_z_of_a_kind([3, 2])
pair_and_four_of_a_kind = x_y_z_of_a_kind([4, 2])
pair_and_five_of_a_kind = x_y_z_of_a_kind([5, 2])
two_three_of_a_kinds = x_y_z_of_a_kind([3, 3])
three_of_a_kind_and_two_pairs = x_y_z_of_a_kind([3, 3, 2])
three_of_a_kind_and_four_of_a_kind = x_y_z_of_a_kind([4, 3])

all_even = all_condition(lambda face: face in [DiceValue.TWO, DiceValue.FOUR, DiceValue.SIX])
all_odd = all_condition(lambda face: face in [DiceValue.ONE, DiceValue.THREE, DiceValue.FIVE])
all_greater_than_equal_to_four = all_condition(lambda face: face in [DiceValue.FOUR, DiceValue.FIVE, DiceValue.SIX])
all_greater_than_equal_to_five = all_condition(lambda face: face in [DiceValue.FIVE, DiceValue.SIX])
all_less_than_equal_to_two = all_condition(lambda face: face in [DiceValue.ONE, DiceValue.TWO])

sum_10 = greater_than_equal_to_value(10)
sum_15 = greater_than_equal_to_value(15)
sum_20 = greater_than_equal_to_value(20)
sum_25 = greater_than_equal_to_value(25)
sum_30 = greater_than_equal_to_value(30)
sum_35 = greater_than_equal_to_value(35)
sum_40 = greater_than_equal_to_value(40)
sum_45 = greater_than_equal_to_value(45)

small_straight = constraint_union(
    contains([DiceValue.ONE, DiceValue.TWO, DiceValue.THREE, DiceValue.FOUR]),
    contains([DiceValue.FIVE, DiceValue.TWO, DiceValue.THREE, DiceValue.FOUR]),
    contains([DiceValue.FIVE, DiceValue.SIX, DiceValue.THREE, DiceValue.FOUR]),
)

large_straight = constraint_union(
    contains([DiceValue.ONE, DiceValue.TWO, DiceValue.THREE, DiceValue.FOUR, DiceValue.FIVE]),
    contains([DiceValue.SIX, DiceValue.TWO, DiceValue.THREE, DiceValue.FOUR, DiceValue.FIVE]),
)

grand_straight = contains([DiceValue.ONE, DiceValue.TWO, DiceValue.THREE, DiceValue.FOUR, DiceValue.FIVE, DiceValue.SIX])

pair_of_sixes_and_ones = contains([DiceValue.SIX, DiceValue.SIX, DiceValue.ONE, DiceValue.ONE])
three_sixes_two_ones = contains([DiceValue.SIX, DiceValue.SIX, DiceValue.SIX, DiceValue.ONE, DiceValue.ONE])

any_roll: ConstraintFunc = lambda r: True


def all_different(dice: list[DiceValue]) -> bool:
    face_freq = get_freq_dist(dice)
    return not any(value > 1 for value in face_freq.values())


def four_of_a_kind_three_ones(dice: list[DiceValue]) -> bool:
    face_freq = get_freq_dist(dice)
    if DiceValue.ONE not in face_freq or face_freq[DiceValue.ONE] < 3:
        return False
    face_freq[DiceValue.ONE] -= 3
    if max(face_freq.values()) < 4:
        return False
    return True


class Constraint:
    def __init__(self, name: str, function: ConstraintFunc) -> None:
        self.name = name
        self.function = function

    def __str__(self) -> str:
        return self.name
    __repr__ = __str__


pair_constraint = Constraint("Pair", pair)
three_of_a_kind_constraint = Constraint("3 of a Kind", three_of_a_kind)
four_of_a_kind_constraint = Constraint("4 of a Kind", four_of_a_kind)
five_of_a_kind_constraint = Constraint("5 of a Kind", five_of_a_kind)
six_of_a_kind_constraint = Constraint("6 of a Kind", six_of_a_kind)
seven_of_a_kind_constraint = Constraint("7 of a Kind", seven_of_a_kind)
two_pairs_constraint = Constraint("2 Pairs", two_pairs)
three_pairs_constraint = Constraint("3 Pairs", three_pairs)
pair_and_three_of_a_kind_constraint = Constraint("Pair & 3 of a Kind", pair_and_three_of_a_kind)
pair_and_four_of_a_kind_constraint = Constraint("Pair & 4 of a Kind", pair_and_four_of_a_kind)
pair_and_five_of_a_kind_constraint = Constraint("Pair & 5 of a Kind", pair_and_five_of_a_kind)
two_three_of_a_kinds_constraint = Constraint("2 3 of a Kinds", two_three_of_a_kinds)
three_of_a_kind_and_two_pairs_constraint = Constraint("3 of a Kind & 2 Pairs", three_of_a_kind_and_two_pairs)
three_of_a_kind_and_four_of_a_kind_constraint = Constraint("3 of a Kind & 4 of a Kind", three_of_a_kind_and_four_of_a_kind)
all_even_constraint = Constraint("All Even", all_even)
all_odd_constraint = Constraint("All Odd", all_odd)
all_greater_than_equal_to_four_constraint = Constraint("All Dice ≥ 4", all_greater_than_equal_to_four)
all_greater_than_equal_to_five_constraint = Constraint("All Dice ≥ 5", all_greater_than_equal_to_five)
all_less_than_equal_to_two_constraint = Constraint("All Dice ≤ 2", all_less_than_equal_to_two)
sum_10_constraint = Constraint("10+", sum_10)
sum_15_constraint = Constraint("15+", sum_15)
sum_20_constraint = Constraint("20+", sum_20)
sum_25_constraint = Constraint("25+", sum_25)
sum_30_constraint = Constraint("30+", sum_30)
sum_35_constraint = Constraint("35+", sum_35)
sum_40_constraint = Constraint("40+", sum_40)
sum_45_constraint = Constraint("45+", sum_45)
small_straight_constraint = Constraint("1234/2345/3456", small_straight)
large_straight_constraint = Constraint("12345/23456", large_straight)
grand_straight_constraint = Constraint("123456", grand_straight)
pair_of_sixes_and_ones_constraint = Constraint("Pair of 6s & Pair of 1s", pair_of_sixes_and_ones)
three_sixes_two_ones_constraint = Constraint("3 6s & Pair of 1s", three_sixes_two_ones)
all_different_constraint = Constraint("All Different", all_different)
four_of_a_kind_three_ones_constraint = Constraint("4 of a Kind & 3 1s", four_of_a_kind_three_ones)

row1a = [three_of_a_kind_constraint, pair_constraint, all_even_constraint, sum_10_constraint]
row1b = [three_of_a_kind_constraint, all_greater_than_equal_to_four_constraint, all_odd_constraint, sum_15_constraint]

row2a = [four_of_a_kind_constraint, small_straight_constraint, two_pairs_constraint, sum_20_constraint]
row2b = [four_of_a_kind_constraint, all_greater_than_equal_to_five_constraint, pair_of_sixes_and_ones_constraint, all_different_constraint]

row3a = [five_of_a_kind_constraint, large_straight_constraint, pair_and_three_of_a_kind_constraint, sum_25_constraint]
row3b = [five_of_a_kind_constraint, all_less_than_equal_to_two_constraint, three_sixes_two_ones_constraint, all_different_constraint]

row4a = [six_of_a_kind_constraint, three_pairs_constraint, pair_and_four_of_a_kind_constraint, sum_30_constraint]
row4b = [six_of_a_kind_constraint, grand_straight_constraint, two_three_of_a_kinds_constraint, sum_35_constraint]

row5a = [seven_of_a_kind_constraint, three_of_a_kind_and_two_pairs_constraint,
         three_of_a_kind_and_four_of_a_kind_constraint, sum_40_constraint]
row5b = [seven_of_a_kind_constraint, four_of_a_kind_three_ones_constraint,
         pair_and_five_of_a_kind_constraint, sum_45_constraint]

a_rows = [row1a, row2a, row3a, row4a, row5a]
b_rows = [row1b, row2b, row3b, row4b, row5b]
any_roll_constraint = Constraint("Any Roll", any_roll)

if __name__ == "__main__":
    print(three_pairs_constraint.function([DiceValue.FOUR]*4+[DiceValue.TWO]*2))
