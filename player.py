from __future__ import annotations
from collections.abc import Callable
import random
from dice import Die, PipUpException, get_die
from display import COLOR
from enums import *
from game_io import IOPort
from tile import ActionFunction, Effect, SelectionException, RearrangementException, Tile
from constraint import pair_constraint

from typing import TYPE_CHECKING, TypeVar
if TYPE_CHECKING:
    from main import Game


class Action:
    def __init__(self, name: str, func: ActionFunction) -> None:
        self.name = name
        self.function = func


def pipup_function(player: Player, game: Game):
    if ScarabType.PIPUP not in player.tokens:
        raise Exception("No pip-up scarab!")
    player.io.choose_die(player.available_dice, message="Choose die to pipup:").pipup(1)
    player.tokens.remove(ScarabType.PIPUP)


def reroll_function(player: Player, game: Game):
    if ScarabType.REROLL not in player.tokens:
        raise Exception("No reroll scarab!")
    player.io.choose_die(player.available_dice, message="Choose die to reroll:").roll()
    player.tokens.remove(ScarabType.REROLL)


pipup_color = 5
reroll_color = 2
pipup_action = Action(f"Use {COLOR(pipup_color, "Pip-up")} Token", pipup_function)
reroll_action = Action(f"Use {COLOR(reroll_color, "Reroll")} Token", reroll_function)

DiceConstraint = Callable[[Die], bool]


T = TypeVar('T')


class Player:
    def __init__(self, tiles: list[Tile], name: tuple[str, int], io: IOPort, starting_tokens: int = 0) -> None:
        self._tiles = tiles
        self.io = io
        self.available_dice: list[Die] = []
        self.locked_dice: list[Die] = []
        self.prepared_dice: list[Die] = []
        self.tokens: list[ScarabType] = []
        self.add_scarabs(starting_tokens)

        self.effects: list[Effect] = []
        self.step = TurnStep.NONE
        self.locked_pair = False
        self.borrowed_tile: Tile | None = None

        self.final_score = (0, 0)
        self.finished = False

        self.name, self.color = name

    @property
    def tiles(self):
        return self._tiles + ([self.borrowed_tile] if self.borrowed_tile is not None else [])

    @property
    def pip_up_amount(self):
        return self.tokens.count(ScarabType.PIPUP)

    @property
    def reroll_amount(self):
        return self.tokens.count(ScarabType.REROLL)

    @property
    def token_count(self):
        return len(self.tokens)

    @property
    def locked_all(self):
        return not self.available_dice and not self.prepared_dice

    def add_scarabs(self, amount: int):
        for _ in range(amount):
            self.tokens.append(random.choice([ScarabType.PIPUP, ScarabType.REROLL]))

    def add_effect(self, effect: Effect):
        self.effects.append(effect)

    def add_tile(self, tile: Tile):
        self._tiles.append(tile)

    def resolve_powers_rolled(self, game: Game):
        powers_triggered = [die for die in self.available_dice if die.power_triggered]
        while powers_triggered:
            if len(self.powers_rolled) > 1:
                die = self.io.choose_item("Choose a dice power to use:", powers_triggered)

            else:
                die = powers_triggered.pop()
            face = die.face
            die.power_triggered = False
            if face == DiceFace.REROLL:
                die_to_roll = self.io.choose_die(self.available_dice, message="Choose die to reroll:")
                die_to_roll.roll()
            if face in [DiceFace.STAR, DiceFace.STAR_ONE, DiceFace.STAR_DECREE, DiceFace.TWO_STAR]:
                amount = 2 if face == DiceFace.TWO_STAR else 1
                response = self.io.choose_dice(
                    self.available_dice, 0, maximum=amount, message=f"Choose up to {"two dice" if face == DiceFace.TWO_STAR else "one die"} to adjust:")
                for die_to_adjust in response:
                    new_face = self.io.choose_adjust_face(die_to_adjust)
                    die_to_adjust.set_face(new_face)

            powers_triggered = [die for die in self.available_dice if die.power_triggered]
            self.io.show_player_state(self, game)

    def get_active_tiles(self, game: Game):
        return [tile for tile in self.tiles if tile.ability.activation is not None and not tile.disabled and self.step in tile.ability.activation_window and tile.ability.activation_restriction(self, game)]

    def query_optional_activations(self, game: Game):
        for tile in self.get_active_tiles(game):
            if self.io.choose_item(f"Activate {tile}?", ["Yes", "No"]) == "Yes":
                assert tile.ability.activation is not None
                tile.activate(self, game)

    def activate_all(self, game: Game):
        for tile in self.get_active_tiles(game):
            assert tile.ability.activation is not None
            tile.activate(self, game)

    def claim_tile(self, game: Game, dice: list[Die], restriction: Callable[[Tile], bool] = lambda t: True):
        self.step = TurnStep.CLAIM
        dice_values = [to_value(die.face) for die in dice if to_value(die.face) != DiceValue.NULL]
        dice_amount = len(dice)
        tile_options: list[Tile] = []
        for tile, condition in game.get_tiles_conditions():
            if tile not in self.tiles and game.tile_available(tile) and dice_amount >= tile.level and condition.function(dice_values) and restriction(tile):
                tile_options.append(tile)
        if tile_options:
            tile_to_claim = self.io.choose_item("Choose a tile:", tile_options)
            game.claim_tile(self, tile_to_claim)
            self.query_optional_activations(game)
        else:
            self.io.show_message(f"{self} couldn't claim any tiles! They recieved 2 tokens as compensation.")
            self.add_scarabs(2)

    def score(self, game: Game):
        values = [die.value.value for die in self.locked_dice if die.value is not DiceValue.NULL]
        scores = [(values.count(i), i) for i in set(values)]
        scores.append(self.final_score)
        self.final_score = sorted(scores, reverse=True)[0]
        game.submit_score(self)

    def take_turn(self, game: Game):
        # Reset Dice Zones
        self.available_dice = []
        self.locked_dice = []
        self.prepared_dice = []

        # Turn Start
        self.io.show_player_state(self, game)
        self.step = TurnStep.TURN_START
        for tile in self.tiles:
            if tile.type in [TileType.YELLOW, TileType.BLUE]:
                tile.disabled = False
            if tile.ability.turn_start is not None:
                tile.ability.turn_start(self, game, tile)
                tile.value = 0

        self.query_optional_activations(game)
        if game.final_roll_off:
            self.step = TurnStep.ROLL_OFF_START
            self.query_optional_activations(game)

        for effect in self.effects:
            effect.turn_start(self, game)
        self.effects = []
        while self.prepared_dice:
            # Roll
            self.step = TurnStep.ROLLS
            for die in self.prepared_dice:
                die.roll()
                self.available_dice.append(die)
            self.prepared_dice = []

            for tile in self.tiles:
                tile.value_up()

            # Action Phase
            while True:
                actions: list[Action] = []
                if ScarabType.PIPUP in self.tokens:
                    actions.append(pipup_action)
                if ScarabType.REROLL in self.tokens:
                    actions.append(reroll_action)
                for tile in self.get_active_tiles(game):
                    actions.append(Action(f"Activate {tile}", tile.activate))

                self.io.show_player_state(self, game)

                self.powers_rolled = [die.face for die in self.available_dice if die.face in Die.power_faces]
                self.resolve_powers_rolled(game)

                choice = self.io.choose_item("Choose an Action:", actions+["lock"])

                if choice == "lock":
                    self.step = TurnStep.LOCK
                    dice_to_lock = self.io.choose_dice(self.available_dice, 0, maximum=None, message="Choose Dice to Lock")
                    dice_to_reroll = [die for die in self.available_dice if die not in dice_to_lock]
                    if any(die.dice_type == DiceType.IMMEDIATE for die in dice_to_reroll):
                        self.io.show_message("Immediate Dice must be locked.")
                        continue
                    if not dice_to_lock:
                        if not self.available_dice:
                            break
                        self.io.show_message("Dice Locking cancelled.")
                        continue
                    self.locked_dice.extend(dice_to_lock)
                    self.prepared_dice.extend(dice_to_reroll)
                    self.available_dice = []

                    for die in dice_to_lock:
                        if die.face is DiceFace.ADD_TWO:
                            self.prepared_dice.extend([get_die(DiceType.STANDARD) for _ in range(2)])
                        if die.face is DiceFace.STAR_DECREE:
                            copiable_tiles = [tile for opponent in game.get_opponents(
                                self) for tile in opponent.tiles if tile not in self.tiles]
                            if copiable_tiles:
                                self.borrowed_tile = self.io.choose_item("Choose Tile to Copy:", copiable_tiles).clone()

                    self.locked_pair = pair_constraint.function([die.value for die in dice_to_lock if die.value is not DiceValue.NULL])
                    self.query_optional_activations(game)
                    self.locked_pair = False
                    break

                if isinstance(choice, str):
                    raise ValueError(f"Invalid Choice value: {choice}")
                selected_action: Action = choice

                self.io.show_message(f"You chose: {selected_action.name}")

                try:
                    selected_action.function(self, game)
                    self.resolve_powers_rolled(game)
                except SelectionException as e:
                    self.io.show_message(e.args[0])
                except PipUpException:
                    self.io.show_message("Can't pip-up that die!")
                except RearrangementException:
                    self.io.show_message("Rearrangement Failed!")
        self.borrowed_tile = None

        # Claim Phase
        self.io.show_player_state(self, game)
        if not game.final_roll_off:
            self.claim_tile(game, self.locked_dice)
            self.step = TurnStep.CLAIM_END
            self.query_optional_activations(game)
        else:
            self.step = TurnStep.ROLL_OFF_END
            self.finished = True
            self.query_optional_activations(game)
            if self.finished:
                self.score(game)

        self.step = TurnStep.NONE

    def __str__(self) -> str:
        return COLOR(self.color, self.name)
    __repr__ = __str__
