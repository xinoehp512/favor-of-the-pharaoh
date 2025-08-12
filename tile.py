from __future__ import annotations
from collections.abc import Callable
from dice import Die, get_die
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


def add_wild_die(player: Player, game: Game, tile: Tile):
    print("Choose the dice value")
    face = player.agent.choose_item(sorted(get_die(DiceType.STANDARD).faces, key=lambda v: v.value))
    player.available_dice.append(get_die(DiceType.STANDARD).set_face(face))


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
    face = player.agent.choose_item(sorted(get_die(DiceType.STANDARD).faces, key=lambda v: v.value))
    player.locked_dice.append(get_die(DiceType.STANDARD).set_face(face))


def free_adjust_types(condition: Callable[[Die], bool]):
    def func(player: Player, game: Game, tile: Tile):
        dice_to_adjust = player.agent.choose_dice(player, game, 0, maximum=None,
                                                  message="Choose dice to adjust", constraint=condition)
        for die in dice_to_adjust:
            player.agent.adjust_die_to_other(die)
    return func


def master_artisan_ability(player: Player, game: Game, tile: Tile):
    die_to_adjust = player.agent.choose_dice(player, game, 1, message="Choose die to adjust")[0]
    player.agent.adjust_die_to_other(die_to_adjust)


def plus_x_to_all(x: int):
    def func(player: Player, game: Game, tile: Tile):
        chosen_dice = player.agent.choose_dice(player, game, 0, maximum=None,
                                               message=f"Choose dice to add {x} to:", constraint=lambda d: d.can_pipup_x(x))
        for die in chosen_dice:
            die.pipup(x)
    return func


def bad_omen_ability(player: Player, game: Game, tile: Tile):
    def add_red(player: Player, game: Game):
        player.prepared_dice.append(get_die(DiceType.STANDARD))

    def remove_any_2(player: Player, game: Game):
        if player.step == TurnStep.ROLL_OFF_START:
            return
        dice_to_lose = player.agent.choose_dice(player, game, 2, message="Choose dice to lose for the turn", source=player.prepared_dice)
        for die in dice_to_lose:
            player.prepared_dice.remove(die)
    player.add_effect(Effect(add_red))
    for opponent in game.get_opponents(player):
        opponent.add_effect(Effect(remove_any_2))


def surveyor_ability(player: Player, game: Game, tile: Tile):
    split_die = player.agent.choose_dice(player, game, 1, message="Choose dice to split:",
                                         constraint=lambda d: is_numeric(d.face) and to_value(d.face).value > 1)[0]
    player.available_dice.remove(split_die)
    new_dice = player.agent.choose_rearrangement(player, game, [get_die(DiceType.IMMEDIATE)
                                                 for _ in range(2)], to_value(split_die.face).value)
    for die, face in new_dice:
        player.available_dice.append(die.set_face(face))


def secret_passage_ability(player: Player, game: Game, tile: Tile):
    lv_3_tiles = game.get_available_tiles(player, lambda tile: tile.level == 3)
    try:
        choices = player.agent.choose_items("Choose 2 Level 3 Tiles:", lv_3_tiles, 0, 2)
    except ValueError:
        choices = lv_3_tiles
    if not choices:
        print("No Tiles Claimed!")
        return
    for choice in choices:
        game.claim_tile(player, choice)


def treasure_ability(player: Player, game: Game, tile: Tile):
    group_1 = player.agent.choose_dice(
        player, game, 1, None, message="Select dice for group 1 (the rest will be in group 2):", source=player.locked_dice)
    group_2 = [die for die in player.locked_dice if die not in group_1]
    tile.disabled = True
    player.claim_tile(game, group_1, restriction=lambda tile: tile.type is not TileType.RED)
    player.claim_tile(game, group_2, restriction=lambda tile: tile.type is not TileType.RED)


def royal_mother_ability(player: Player, game: Game, tile: Tile):
    swap_dice = player.agent.choose_dice(player, game, 0, None, message="Choose any number of Immediate and Serf dice to replace:",
                                         constraint=lambda d: d.dice_type in (DiceType.IMMEDIATE, DiceType.SERF))
    player.add_scarabs(len(swap_dice))
    for die in swap_dice:
        player.available_dice.remove(die)
        player.prepared_dice.append(get_die(DiceType.STANDARD))


def queens_favor_ability(player: Player, game: Game, tile: Tile):
    try:
        choice = player.agent.choose_items("Choose any blue or yellow tile Level 6 or lower.", game.get_available_tiles(
            player, lambda tile: tile.level <= 6 and tile.type is not TileType.RED), 1)[0]
        game.claim_tile(player, choice)
    except:
        print("No tiles remain!")
    game.set_next_turn(player)


def royal_power_ability(player: Player, game: Game, tile: Tile):
    try:
        choices = player.agent.choose_items("Choose up to 2 blue tiles Level 6 or lower.", game.get_available_tiles(
            player, lambda tile: tile.level <= 6 and tile.type is TileType.BLUE), 0, 2)
        for choice in choices:
            game.claim_tile(player, choice)
    except:
        print("No tiles remain!")
        return


def queen_claim(player: Player, game: Game, tile: Tile):
    player.score(game)
    game.begin_final_roll_off()


def pharaohs_gift_ability(player: Player, game: Game, tile: Tile):
    player.final_score = (0, 0)
    player.finished = False
    game.set_next_turn(player)


def royal_death_ability(player: Player, game: Game, tile: Tile):
    def add_2_grey(player: Player, game: Game):
        player.prepared_dice.extend([get_die(DiceType.IMMEDIATE) for _ in range(2)])
    player.add_effect(Effect(add_2_grey))
    game.set_next_turn(player)
    game.begin_final_roll_off()


class Tile:
    tile_color_dict = {
        TileType.YELLOW: 226,
        TileType.BLUE: 20,
        TileType.RED: 196
    }

    def __init__(self, name: str, description: str, level: int, type: TileType, ability: Ability = Ability()) -> None:
        self.name = name
        self.description = description
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
        return Tile(self.name, self.description, self.level, self.type, self.ability)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Tile) and value.name == self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return COLOR(Tile.tile_color_dict[self.type], self.name)
    __repr__ = __str__


farmer = Tile("FARMER", 'Roll +1 Standard die to start your turn.', 3, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.STANDARD])))
guard = Tile("GUARD", 'After any roll, may bring 1 Standard die into play as a "2".', 3, TileType.YELLOW, ability=Ability(
    activation_function=add_value_die(DiceFace.TWO)))
indentured_worker = Tile("INDENTURED WORKER", 'When claimed, gain 1 token. Roll +1 Immediate die to start your turn.', 3, TileType.YELLOW, ability=Ability(
    on_claim_function=add_scarabs(1),
    turn_start_function=add_roll_dice([DiceType.IMMEDIATE])))
serf = Tile("SERF", 'Roll +1 Serf die to start your turn.', 3, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.SERF])))
worker = Tile("WORKER", 'After a roll, may bring 1 Standard die into play as a "1".', 3, TileType.YELLOW, ability=Ability(
    activation_function=add_value_die(DiceFace.ONE)))
beggar = Tile("BEGGAR", 'Each turn, gain 1 token before your first roll.', 3, TileType.BLUE, ability=Ability(
    turn_start_function=add_scarabs(1)))
servant = Tile("SERVANT", 'Add 1, 2, or 3 pips to an active die.', 3, TileType.BLUE, ability=Ability(
    activation_function=servant_ability))
soothsayer = Tile("SOOTHSAYER", 'Move any number of pips between two active dice.', 3, TileType.BLUE, ability=Ability(
    activation_function=rearrange_dice(2)))
ankh = Tile("ANKH", 'Gain tokens equal to the number of tokens you have.', 3, TileType.RED, ability=Ability(
    activation_function=ankh_ability))
omen = Tile("OMEN", 'After claiming this tile, immediately take another turn, rolling 1 Standard die fewer than normal to start it.', 3, TileType.RED, ability=Ability(
    on_claim_function=omen_ability))
ancestral_guidance = Tile("ANCESTRAL GUIDANCE", 'Gain 2 tokens immediately when used and +1 Standard die to roll.', 3, TileType.RED, ability=Ability(
    activation_function=both(add_roll_dice([DiceType.STANDARD]), add_scarabs(2))))

artisan = Tile("ARTISAN", 'Roll +1 Artisan die to start your turn.', 4, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.ARTISAN])))
builder = Tile("BUILDER", 'Each turn, gain 1 token before your first roll. Roll +1 Immediate die to start your turn.', 4, TileType.YELLOW, ability=Ability(
    turn_start_function=both(add_roll_dice([DiceType.IMMEDIATE]), add_scarabs(1))))
noble_adoption = Tile("NOBLE ADOPTION", 'Roll +1 Noble die to start your turn.', 4, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.NOBLE])))
palace_servants = Tile("PALACE SERVANTS", 'Roll +2 Immediate dice to start your turn.', 4, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.IMMEDIATE for _ in range(2)])))
soldier = Tile("SOLDIER", 'After any roll, may bring 1 Standard die into play as a "3".', 4, TileType.YELLOW, ability=Ability(
    activation_function=add_value_die(DiceFace.THREE)))
grain_merchant = Tile("GRAIN MERCHANT", 'Reroll 1+ active dice to gain 1 token.', 4, TileType.BLUE, ability=Ability(
    activation_function=grain_merchant_ability))
entertainer = Tile("ENTERTAINER", 'Flip any number of dice, including Custom dice, upside down.', 4, TileType.BLUE, ability=Ability(
    activation_function=entertainer_ability))
matchmaker = Tile("MATCHMAKER", 'Adjust 1 active die to match any locked die.', 4, TileType.BLUE, ability=Ability(
    activation_function=matchmaker_ability))
good_omen = Tile("GOOD OMEN", 'After claiming this tile, immediately take another turn.', 4, TileType.RED, ability=Ability(
    on_claim_function=good_omen_ability))
palace_key = Tile("PALACE KEY", 'Roll +2 Standard dice to start your turn.', 4, TileType.RED, ability=Ability(
    activation_function=add_roll_dice([DiceType.STANDARD for _ in range(2)]),
    activation_window=[TurnStep.TURN_START]))
spirit_of_the_dead = Tile("SPIRIT OF THE DEAD", 'After locking all rolled dice, gain +1 Standard die, adjust it to any face, and lock it.', 4, TileType.RED, ability=Ability(
    activation_function=add_locked_wild_die,
    activation_restriction=lambda p, g: p.locked_all,
    activation_window=[TurnStep.LOCK]))

charioteer = Tile("CHARIOTEER", 'After any roll, may bring 1 Standard die into play as a "5".', 5, TileType.YELLOW, ability=Ability(
    activation_function=add_value_die(DiceFace.FIVE)))
conspirator = Tile("CONSPIRATOR", 'Roll +1 Intrigue die to start your turn.', 5, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.INTRIGUE])))
overseer = Tile("OVERSEER", 'After any roll, may bring 1 Standard die into play as a "4".', 5, TileType.YELLOW, ability=Ability(
    activation_function=add_value_die(DiceFace.FOUR)))
ship_captain = Tile("SHIP CAPTAIN", 'Roll +1 Voyage die to start your turn.', 5, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.VOYAGE])))
tomb_builder = Tile("TOMB BUILDER", 'Each turn, gain 1 token before your first roll. Roll +1 Standard die to start your turn.', 5, TileType.YELLOW, ability=Ability(
    turn_start_function=both(add_roll_dice([DiceType.STANDARD]), add_scarabs(1))))
head_servant = Tile("HEAD SERVANT", 'Adjust any number of active Immediate dice to any face(s).', 5, TileType.BLUE, ability=Ability(
    activation_function=free_adjust_types(lambda d: d.dice_type == DiceType.IMMEDIATE)))
master_artisan = Tile("MASTER ARTISAN", 'Adjust 1 active die to any other face.', 5, TileType.BLUE, ability=Ability(
    activation_function=master_artisan_ability))
priest = Tile("PRIEST", 'Add 1 pip to any number of active dice.', 5, TileType.BLUE, ability=Ability(
    activation_function=plus_x_to_all(1)))
bad_omen = Tile("BAD OMEN", 'Play after your turn. Each other player rolls -2 dice next non-rolloff turn. Roll +1 Standard die next turn.', 5, TileType.RED, ability=Ability(
    activation_function=bad_omen_ability,
    activation_window=[TurnStep.CLAIM_END]))
burial_mask = Tile("BURIAL MASK", 'Gain 5 tokens.', 5, TileType.RED, ability=Ability(
    activation_function=add_scarabs(5)))
royal_decree = Tile("ROYAL DECREE", 'Roll +3 Immediate dice to start your final roll-off turn.', 5, TileType.RED, ability=Ability(
    activation_function=add_roll_dice([DiceType.IMMEDIATE for _ in range(3)]),
    activation_window=[TurnStep.ROLL_OFF_START]))

embalmer = Tile("EMBALMER", 'After any roll, may bring 1 Standard die into play as a "6".', 6, TileType.YELLOW, ability=Ability(
    activation_function=add_value_die(DiceFace.SIX)))
estate_overseer = Tile("ESTATE OVERSEER", 'Each turn, gain 1 token. After any roll, may bring 1 incrementing Standard die into play.', 6, TileType.YELLOW, ability=Ability(
    turn_start_function=add_scarabs(1),
    activation_function=add_incremental_die))
grain_trader = Tile("GRAIN TRADER", 'Each turn, gain 2 tokens before your first roll. Roll +1 Standard die to start your turn.', 6, TileType.YELLOW, ability=Ability(
    turn_start_function=both(add_roll_dice([DiceType.STANDARD]), add_scarabs(2))))
priest_of_the_dead = Tile("PRIEST OF THE DEAD", 'After locking all rolled dice, gain +1 Standard die, adjust it to any face, and lock it.', 6, TileType.YELLOW, ability=Ability(
    activation_function=add_locked_wild_die,
    activation_restriction=lambda p, g: p.locked_all,
    activation_window=[TurnStep.LOCK]))
royal_attendants = Tile("ROYAL ATTENDANTS", 'Roll +1 Standard die and +1 Immediate die to start your turn.', 6, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.STANDARD, DiceType.IMMEDIATE])))
astrologer = Tile("ASTROLOGER", 'Move any number of pips among up to three active dice.', 6, TileType.BLUE, ability=Ability(
    activation_function=rearrange_dice(3)))
priestess = Tile("PRIESTESS", 'Add exactly 2 pips to any number of active dice.', 6, TileType.BLUE, ability=Ability(
    activation_function=plus_x_to_all(2)))
surveyor = Tile("SURVEYOR", 'Replace 1 active die with 2 Immediate dice, whose pips must sum to the number of pips of the die being replaced.', 6, TileType.BLUE, ability=Ability(
    activation_function=surveyor_ability))
pharaohs_gift = Tile("PHARAOH'S GIFT", 'After your final roll-off turn, redo your final roll-off.', 6, TileType.RED, ability=Ability(
    activation_function=pharaohs_gift_ability,
    activation_window=[TurnStep.ROLL_OFF_END]))
secret_passage = Tile("SECRET PASSAGE", "Claim up to two level 3 tiles that you don't already have.", 6, TileType.RED, ability=Ability(
    activation_function=secret_passage_ability,
    activation_window=[TurnStep.ROLLS, TurnStep.CLAIM_END]))
treasure = Tile("TREASURE", "Use after claiming a tile (including possibly this one). Divide your locked dice into two groups. With each group, claim one yellow or blue tile that you don't already have.", 6, TileType.RED, ability=Ability(
    activation_function=treasure_ability,
    activation_window=[TurnStep.CLAIM]))

general = Tile("GENERAL", 'Roll +2 Standard dice to start your turn.', 7, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.STANDARD for _ in range(2)])))
grand_vizier = Tile("GRAND VIZIER", 'Roll +1 Decree die to start your turn.', 7, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.DECREE])))
granary_master = Tile("GRANARY MASTER", 'Roll +1 Standard die to start your turn. After any roll, may bring 1 incrementing Standard die into play.', 7, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.STANDARD]),
    activation_function=add_incremental_die))
heir = Tile("HEIR", 'Add 1 pip to any number of active dice, then add 1 pip to any number of active dice.', 7, TileType.BLUE, ability=Ability(activation_function=both(
    plus_x_to_all(1), plus_x_to_all(1))))
royal_astrologer = Tile("ROYAL ASTROLOGER", 'Adjust any number of active non-Standard dice to any other face(s).', 7, TileType.BLUE, ability=Ability(
    activation_function=free_adjust_types(lambda d: d.dice_type != DiceType.STANDARD)))
royal_mother = Tile("ROYAL MOTHER", 'Replace any number of active Immediate and/or Serf dice with an equal number of tokens and Standard dice to roll.', 7, TileType.BLUE, ability=Ability(
    activation_function=royal_mother_ability))
queens_favor = Tile("QUEEN'S FAVOR", "Play immediately. Claim any yellow or blue tile of level 6 or lower that you don't already have and then immediately take another turn.", 7, TileType.RED, ability=Ability(
    on_claim_function=queens_favor_ability))
royal_death = Tile("ROYAL DEATH", 'Play immediately. You begin the final roll-off, rolling +2 Immediate dice.', 7, TileType.RED, ability=Ability(
    on_claim_function=royal_death_ability))
royal_power = Tile("ROYAL POWER", "Claim up to two blue tiles of level 6 or lower that you don't already have.", 7, TileType.RED, ability=Ability(
    activation_function=royal_power_ability,
    activation_window=[TurnStep.ROLLS, TurnStep.CLAIM_END]))

queen = Tile("QUEEN", 'When claimed, take the Pharaoh token. After any roll, may bring 1 Standard die of any value into play.', 7, TileType.YELLOW, ability=Ability(
    activation_function=add_wild_die,
    on_claim_function=queen_claim))
herder = Tile("HERDER", 'After locking a pair, may gain +1 Standard die to Roll.', 1, TileType.YELLOW, ability=Ability(
    activation_function=add_roll_dice([DiceType.STANDARD]),
    activation_restriction=lambda p, g: p.locked_pair,
    activation_window=[TurnStep.LOCK]))
start = Tile("START", 'Once per turn, after locking 2 or more matching dice on one roll, gain +1 Standard die to roll.', 0, TileType.YELLOW, ability=Ability(
    turn_start_function=add_roll_dice([DiceType.STANDARD for _ in range(3)])))

tiles = [farmer, guard, indentured_worker, serf, worker, beggar, servant, soothsayer, ankh, omen, ancestral_guidance, artisan, builder, noble_adoption, palace_servants, soldier, grain_merchant, entertainer, matchmaker, good_omen, palace_key, spirit_of_the_dead, charioteer, conspirator, overseer, ship_captain, tomb_builder, head_servant,
         master_artisan, priest, bad_omen, burial_mask, royal_decree, embalmer, estate_overseer, grain_trader, priest_of_the_dead, royal_attendants, astrologer, priestess, surveyor, pharaohs_gift, secret_passage, treasure, general, grand_vizier, granary_master, heir, royal_astrologer, royal_mother, queens_favor, royal_death, royal_power]
