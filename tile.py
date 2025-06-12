from __future__ import annotations
from collections.abc import Callable
from dice import get_die
from display import COLOR
from enums import *

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import Game
    from player import Player


AbilityFunction = Callable[['Player', 'Game', 'Tile'], None]
ActionFunction = Callable[['Player', 'Game'], None]
GameConstraint = Callable[['Player', 'Game'], bool]


class SelectionException(Exception):
    pass


class RearrangementException(Exception):
    pass


class Ability:
    def __init__(self,
                 turn_start_function: AbilityFunction | None = None,
                 activation_function: AbilityFunction | None = None,
                 on_claim_function: AbilityFunction | None = None,
                 activation_restriction: GameConstraint = lambda p, g: True,
                 activation_window: list[TurnStep] = [TurnStep.ROLLS]) -> None:
        self.turn_start = turn_start_function
        self.activation = activation_function
        self.on_claim = on_claim_function

        self.activation_restriction = activation_restriction
        self.activation_window = activation_window


class Effect:
    def __init__(self, turn_start_function: ActionFunction) -> None:
        self.turn_start = turn_start_function


def add_roll_dice(dice: list[DiceType]):
    def func(player: Player, game: Game, tile: Tile):
        [player.prepared_dice.append(get_die(die)) for die in dice]
    return func


def add_scarabs(amount: int):
    def func(player: Player, game: Game, tile: Tile):
        player.add_scarabs(amount)
    return func


def add_value_die(face: DiceFace):
    def func(player: Player, game: Game, tile: Tile):
        player.available_dice.append(get_die(DiceType.STANDARD).set_face(face))
    return func


def add_incremental_die(player: Player, game: Game, tile: Tile):
    player.available_dice.append(get_die(DiceType.STANDARD).set_face(DiceFace(tile.value)))


def both(*args: AbilityFunction):
    def func(player: Player, game: Game, tile: Tile):
        for f in args:
            f(player, game, tile)
    return func


def servant_ability(player: Player, game: Game, tile: Tile):
    chosen_die = player.agent.choose_dice(player, game, 1, message="Choose die to pipup:")[0]
    amount = player.agent.choose_item([1, 2, 3])
    chosen_die.pipup(amount)


def rearrange_dice(amount: int):
    def func(player: Player, game: Game, tile: Tile):
        chosen_dice = player.agent.choose_dice(player, game, amount, message="Choose dice to rearrange pips:")
        if any(to_value(die.face) is DiceValue.NULL for die in chosen_dice):
            print("Can't move pips on non-numeric faces!")
            raise RearrangementException()
        try:
            total_sum = sum(to_value(die.face).value for die in chosen_dice)
            rearrangement = player.agent.choose_rearrangement(player, game, chosen_dice, total_sum)
            for die, face in rearrangement:
                die.set_face(face)
        except ValueError as e:
            print(e.args)
            raise RearrangementException()
    return func


def ankh_ability(player: Player, game: Game, tile: Tile):
    player.add_scarabs(player.token_count)


def omen_ability(player: Player, game: Game, tile: Tile):
    def remove_red(player: Player, game: Game):
        for die in player.prepared_dice:
            if die.dice_type == DiceType.STANDARD:
                player.prepared_dice.remove(die)
                break
    if player.step == TurnStep.CLAIM:
        game.set_next_turn(player)
        player.add_effect(Effect(remove_red))


def good_omen_ability(player: Player, game: Game, tile: Tile):
    if player.step == TurnStep.CLAIM:
        game.set_next_turn(player)


def grain_merchant_ability(player: Player, game: Game, tile: Tile):
    chosen_dice = player.agent.choose_dice(player, game, 0, maximum=None, message="Choose dice to reroll:")
    if not chosen_dice:
        raise SelectionException()
    for die in chosen_dice:
        die.roll()
    player.add_scarabs(1)


def entertainer_ability(player: Player, game: Game, tile: Tile):
    chosen_dice = player.agent.choose_dice(player, game, 0, maximum=None, message="Choose dice to reroll:")
    for die in chosen_dice:
        die.flip()


def matchmaker_ability(player: Player, game: Game, tile: Tile):
    locked_values = [to_value(die.face) for die in player.locked_dice if to_value(die.face) != DiceValue.NULL]
    possible_matches = [die for die in player.available_dice if any(to_value(face) in locked_values for face in die.faces)]
    if len(possible_matches) == 0:
        raise SelectionException("No possible matches!")
    die_to_adjust = player.agent.choose_dice(player, game, 1, message="Choose a die to match a locked die:")[0]
    print("Choose a face from among locked dice:")
    options = [face for face in die_to_adjust.faces if to_value(face) in locked_values]
    face_to_match = player.agent.choose_item(options)
    die_to_adjust.set_face(face_to_match)


def add_locked_wild_die(player: Player, game: Game, tile: Tile):
    print("Choose the dice value")
    face = player.agent.choose_item(get_die(DiceType.STANDARD).faces)
    player.locked_dice.append(get_die(DiceType.STANDARD).set_face(face))


class Tile:
    tile_color_dict = {
        TileType.YELLOW: 226,
        TileType.BLUE: 20,
        TileType.RED: 196
    }

    def __init__(self, name: str, level: int, type: TileType, ability: Ability = Ability()) -> None:
        self.name = name
        self.level = level
        self.type = type
        self.ability = ability
        self.disabled = False
        self.value = 0

    def activate(self, player: Player, game: Game):
        if self.ability.activation is None or self.disabled:
            raise Exception("Tile can't be activated.")
        self.ability.activation(player, game, self)
        self.disabled = True

    def value_up(self):
        if self.value < 6:
            self.value += 1

    def clone(self):
        return Tile(self.name, self.level, self.type, self.ability)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Tile) and value.name == self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return COLOR(Tile.tile_color_dict[self.type], self.name)
    __repr__ = __str__


farmer = Tile("FARMER", 3, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.STANDARD])))
guard = Tile("GUARD", 3, TileType.YELLOW, ability=Ability(
    activation_function=add_value_die(DiceFace.TWO)))
indentured_worker = Tile("INDENTURED WORKER", 3, TileType.YELLOW, ability=Ability(
    on_claim_function=add_scarabs(1),
    turn_start_function=add_roll_dice([DiceType.IMMEDIATE])))
serf = Tile("SERF", 3, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.SERF])))
worker = Tile("WORKER", 3, TileType.YELLOW, ability=Ability(
    activation_function=add_value_die(DiceFace.ONE)))
beggar = Tile("BEGGAR", 3, TileType.BLUE, ability=Ability(
    turn_start_function=add_scarabs(1)))
servant = Tile("SERVANT", 3, TileType.BLUE, ability=Ability(
    activation_function=servant_ability))
soothsayer = Tile("SOOTHSAYER", 3, TileType.BLUE, ability=Ability(
    activation_function=rearrange_dice(2)))
ankh = Tile("ANKH", 3, TileType.RED, ability=Ability(
    activation_function=ankh_ability))
omen = Tile("OMEN", 3, TileType.RED, ability=Ability(
    on_claim_function=omen_ability))
ancestral_guidance = Tile("ANCESTRAL GUIDANCE", 3, TileType.RED, ability=Ability(
    activation_function=both(add_roll_dice([DiceType.STANDARD]), add_scarabs(2))))

artisan = Tile("ARTISAN", 4, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.ARTISAN])))
builder = Tile("BUILDER", 4, TileType.YELLOW, ability=Ability(
    turn_start_function=both(add_roll_dice([DiceType.IMMEDIATE]), add_scarabs(1))))
noble_adoption = Tile("NOBLE ADOPTION", 4, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.NOBLE])))
palace_servants = Tile("PALACE SERVANTS", 4, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.IMMEDIATE for _ in range(2)])))
soldier = Tile("SOLDIER", 4, TileType.YELLOW, ability=Ability(
    activation_function=add_value_die(DiceFace.THREE)))
grain_merchant = Tile("GRAIN MERCHANT", 4, TileType.BLUE, ability=Ability(
    activation_function=grain_merchant_ability))
entertainer = Tile("ENTERTAINER", 4, TileType.BLUE, ability=Ability(
    activation_function=entertainer_ability))
matchmaker = Tile("MATCHMAKER", 4, TileType.BLUE, ability=Ability(
    activation_function=matchmaker_ability))
good_omen = Tile("GOOD OMEN", 4, TileType.RED, ability=Ability(
    on_claim_function=good_omen_ability))
palace_key = Tile("PALACE KEY", 4, TileType.RED, ability=Ability(
    activation_function=add_roll_dice([DiceType.STANDARD for _ in range(2)]),
    activation_window=[TurnStep.TURN_START]))
spirit_of_the_dead = Tile("SPIRIT OF THE DEAD", 4, TileType.RED, ability=Ability(
    activation_function=add_locked_wild_die,
    activation_restriction=lambda p, g: p.locked_all,
    activation_window=[TurnStep.LOCK]))

charioteer = Tile("CHARIOTEER", 5, TileType.YELLOW, ability=Ability(
    activation_function=add_value_die(DiceFace.FIVE)))
conspirator = Tile("CONSPIRATOR", 5, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.INTRIGUE])))
overseer = Tile("OVERSEER", 5, TileType.YELLOW, ability=Ability(
    activation_function=add_value_die(DiceFace.FOUR)))
ship_captain = Tile("SHIP CAPTAIN", 5, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.VOYAGE])))
tomb_builder = Tile("TOMB BUILDER", 5, TileType.YELLOW, ability=Ability(
    turn_start_function=both(add_roll_dice([DiceType.STANDARD]), add_scarabs(1))))
head_servant = Tile("HEAD SERVANT", 5, TileType.BLUE)
master_artisan = Tile("MASTER ARTISAN", 5, TileType.BLUE)
priest = Tile("PRIEST", 5, TileType.BLUE)
bad_omen = Tile("BAD OMEN", 5, TileType.RED)
burial_mask = Tile("BURIAL MASK", 5, TileType.RED)
royal_decree = Tile("ROYAL DECREE", 5, TileType.RED)

embalmer = Tile("EMBALMER", 6, TileType.YELLOW, ability=Ability(
    activation_function=add_value_die(DiceFace.SIX)))
estate_overseer = Tile("ESTATE OVERSEER", 6, TileType.YELLOW, ability=Ability(
    turn_start_function=add_scarabs(1),
    activation_function=add_incremental_die))
grain_trader = Tile("GRAIN TRADER", 6, TileType.YELLOW, ability=Ability(
    turn_start_function=both(add_roll_dice([DiceType.STANDARD]), add_scarabs(2))))
priest_of_the_dead = Tile("PRIEST OF THE DEAD", 6, TileType.YELLOW)
royal_attendents = Tile("ROYAL ATTENDENTS", 6, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.STANDARD, DiceType.IMMEDIATE])))
astrologer = Tile("ASTROLOGER", 6, TileType.BLUE, ability=Ability(
    activation_function=rearrange_dice(3)))
priestess = Tile("PRIESTESS", 6, TileType.BLUE)
surveyor = Tile("SURVEYOR", 6, TileType.BLUE)
pharaohs_gift = Tile("PHARAOH'S GIFT", 6, TileType.RED)
secret_passage = Tile("SECRET PASSAGE", 6, TileType.RED)
treasure = Tile("TREASURE", 6, TileType.RED)

general = Tile("GENERAL", 7, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.STANDARD for _ in range(2)])))
grand_vizier = Tile("GRAND VIZIER", 7, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.DECREE])))
granary_master = Tile("GRANARY MASTER", 7, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.STANDARD]),
    activation_function=add_incremental_die))
heir = Tile("HEIR", 7, TileType.BLUE)
royal_astrologer = Tile("ROYAL ASTROLOGER", 7, TileType.BLUE)
royal_mother = Tile("ROYAL MOTHER", 7, TileType.BLUE)
queens_favor = Tile("QUEEN'S FAVOR", 7, TileType.RED)
royal_death = Tile("ROYAL DEATH", 7, TileType.RED)
royal_power = Tile("ROYAL POWER", 7, TileType.RED)

queen = Tile("QUEEN", 7, TileType.YELLOW)
herder = Tile("HERDER", 1, TileType.YELLOW)
start = Tile("START", 0, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.STANDARD for _ in range(3)])))

tiles = [farmer, guard, indentured_worker, serf, worker, beggar, servant, soothsayer, ankh, omen, ancestral_guidance, artisan, builder, noble_adoption, palace_servants, soldier, grain_merchant, entertainer, matchmaker, good_omen, palace_key, spirit_of_the_dead, charioteer, conspirator, overseer, ship_captain, tomb_builder, head_servant,
         master_artisan, priest, bad_omen, burial_mask, royal_decree, embalmer, estate_overseer, grain_trader, priest_of_the_dead, royal_attendents, astrologer, priestess, surveyor, pharaohs_gift, secret_passage, treasure, general, grand_vizier, granary_master, heir, royal_astrologer, royal_mother, queens_favor, royal_death, royal_power]
