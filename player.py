from __future__ import annotations
from collections.abc import Callable
import itertools
import random
from dice import Die, PipUpException
from display import COLOR, FOREGROUND, RESET
from enums import *
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
    player.agent.choose_dice(player, game, 1, message="Choose die to pipup:")[0].pipup(1)
    player.tokens.remove(ScarabType.PIPUP)


def reroll_function(player: Player, game: Game):
    if ScarabType.REROLL not in player.tokens:
        raise Exception("No reroll scarab!")
    player.agent.choose_dice(player, game, 1, message="Choose die to reroll:")[0].roll()
    player.tokens.remove(ScarabType.REROLL)


pipup_color = 5
reroll_color = 2
pipup_action = Action(f"Use {COLOR(pipup_color, "Pip-up")} Token", pipup_function)
reroll_action = Action(f"Use {COLOR(reroll_color, "Reroll")} Token", reroll_function)

DiceConstraint = Callable[[Die], bool]


class Agent:
    def __init__(self, name: str, color: int) -> None:
        self.name = name
        self.color = color

    def choose_dice(self, player: Player, game: Game, amount: int, maximum: int | None = -1, message: str = "Choose dice:", constraint: DiceConstraint = lambda d: True, source: list[Die] | None = None) -> list[Die]:

        available_dice = [die for die in (source if source is not None else player.available_dice) if constraint(die)]

        if amount > len(available_dice):
            raise SelectionException(f"Cannot choose {amount} dice from only {len(available_dice)} available.")

        if maximum is None:
            maximum = len(available_dice)

        print(message)
        for idx, die in enumerate(available_dice):
            print(f"{idx + 1}: {die}")

        while True:
            amount_str = str(amount)
            if maximum > amount:
                amount_str = f'{amount} to {maximum}'
            raw_input = input(f"Enter {amount_str} distinct dice numbers (1-{len(available_dice)}), separated by commas: ")
            if amount == 0 and raw_input.lower() == "none":
                return []
            try:
                selections = [int(x.strip()) for x in raw_input.split(',')]
            except ValueError:
                print("Please enter only numbers separated by commas.")
                continue

            if len(selections) != amount and maximum <= amount:
                print(f"Please select exactly {amount} dice.")
                continue

            if len(selections) < amount and maximum > amount:
                print(f"Please select between {amount} and {maximum} dice.")
                continue

            if len(set(selections)) != len(selections):
                print("Duplicate selections detected. All choices must be distinct.")
                continue

            if any(choice < 1 or choice > len(available_dice) for choice in selections):
                print("One or more choices are out of valid range.")
                continue

            chosen_dice = [available_dice[i - 1] for i in selections]
            return chosen_dice

    def choose_item(self, options: list[T], display: Callable[[T], str] = str) -> T:
        """
        Prompts the user to choose an item from the provided options list.

        Args:
            options (List[T]): A list of available options of any type.
            display (Callable[[T], str]): Function to convert an item to a string for display. Defaults to str.

        Returns:
            T: The selected item from the list.
        """
        if not options:
            raise ValueError("No options available to choose from.")

        while True:
            print("\nAvailable options:")
            for i, option in enumerate(options, start=1):
                print(f"{i}: {display(option)}")

            choice = input("Choose an option by number: ").strip()
            if not choice.isdigit():
                print("Please enter a valid number.")
                continue

            index = int(choice)-1
            if 0 <= index and index < len(options):
                return options[index]
            else:
                print("Choice out of range. Try again.")

    def choose_items(self, prompt: str, options: list[T], min_amount: int, max_amount: int | None = -1) -> list[T]:
        if max_amount is None or max_amount > len(options):
            max_amount = len(options)
        if max_amount < min_amount:
            max_amount = min_amount

        print(prompt)
        for idx, option in enumerate(options):
            print(f"{idx}: {option}")

        while True:
            try:
                input_str = input(f"Enter between {min_amount} and {max_amount} distinct number(s), comma-separated: ")
                indices = [int(i.strip()) for i in input_str.split(',')]

                if not (min_amount <= len(indices) <= max_amount):
                    print(f"Please enter between {min_amount} and {max_amount} indices.")
                    continue

                if len(set(indices)) != len(indices):
                    print("Duplicate selections are not allowed.")
                    continue

                if any(i < 0 or i >= len(options) for i in indices):
                    print("One or more indices are out of range.")
                    continue

                return [options[i] for i in indices]
            except ValueError:
                print("Invalid input. Please enter valid integers separated by commas.")

    def choose_rearrangement(self, player: Player, game: Game, dice: list[Die], target_sum: int) -> list[tuple[Die, DiceFace]]:

        def is_valid_face(face: DiceFace) -> bool:
            return face.value in range(1, 7) or face == DiceFace.STAR_ONE

        def face_effective_value(face: DiceFace) -> int:
            return 1 if face == DiceFace.STAR_ONE else face.value

        # Collect valid faces for each die
        valid_face_options: list[list[DiceFace]] = []
        for die in dice:
            valid_faces = [face for face in die.faces if is_valid_face(face)]
            if not valid_faces:
                raise ValueError(f"No valid numeric faces for die: {die}")
            valid_face_options.append(valid_faces)

        # Generate all combinations
        all_combinations = list(itertools.product(*valid_face_options))

        # Filter combinations that match the original sum
        seen_signatures: set[tuple[tuple[int, str], ...]] = set()
        valid_combinations: list[tuple[DiceFace, ...]] = []
        for combo in all_combinations:
            if sum(face_effective_value(face) for face in combo) == target_sum:
                # Create a sorted signature to eliminate equivalent sets
                signature = tuple(sorted((die.dice_type.value, face.name) for die, face in zip(dice, combo)))
                if signature not in seen_signatures:
                    seen_signatures.add(signature)
                    valid_combinations.append(combo)

        if not valid_combinations:
            raise ValueError("No valid rearrangements preserve the original sum.")

        # Present options to user
        print("\nValid rearrangements:")
        for idx, combo in enumerate(valid_combinations):
            faces_str = ', '.join(f"{die.clone().set_face(face)}" for die, face in zip(dice, combo))
            print(f"{idx}: {faces_str}")

        # User selection
        while True:
            try:
                choice = int(input("Choose the index of the rearrangement to use: "))
                if 0 <= choice < len(valid_combinations):
                    selected_faces = valid_combinations[choice]
                    return list(zip(dice, selected_faces))
                else:
                    print("Invalid index. Try again.")
            except ValueError:
                print("Invalid input. Please enter a valid integer.")

    def adjust_die_to_other(self, die_to_adjust: Die):
        face_options = sorted(die_to_adjust.faces, key=lambda f: f.value)
        face_options.remove(die_to_adjust.face)
        print("Choose a new face:")
        new_face = self.choose_item(face_options)
        die_to_adjust.set_face(new_face)

    def __str__(self) -> str:
        return COLOR(self.color, self.name)
    __repr__ = __str__


T = TypeVar('T')


class Player:
    def __init__(self, tiles: list[Tile], agent: Agent, starting_tokens: int = 0) -> None:
        self.tiles = tiles
        self.agent = agent
        self.available_dice: list[Die] = []
        self.locked_dice: list[Die] = []
        self.prepared_dice: list[Die] = []
        self.tokens: list[ScarabType] = []
        self.effects: list[Effect] = []
        self.step = TurnStep.NONE
        self.locked_pair = False
        self.add_scarabs(starting_tokens)

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

    def resolve_powers_rolled(self, game: Game):
        powers_triggered = [die for die in self.available_dice if die.power_triggered]
        while powers_triggered:
            if len(self.powers_rolled) > 1:
                print("Choose a dice power to use:")
                die = self.agent.choose_item(powers_triggered)

            else:
                die = powers_triggered.pop()
            face = die.face
            die.power_triggered = False
            if face == DiceFace.REROLL:
                die_to_roll = self.agent.choose_dice(self, game, 1, message="Choose die to reroll:")[0]
                die_to_roll.roll()
            if face in [DiceFace.STAR, DiceFace.STAR_ONE, DiceFace.STAR_DECREE, DiceFace.TWO_STAR]:
                amount = 2 if face == DiceFace.TWO_STAR else 1
                response = self.agent.choose_dice(
                    self, game, 0, maximum=amount, message=f"Choose up to {"two dice" if face == DiceFace.TWO_STAR else "one die"} to adjust:")
                for die_to_adjust in response:
                    self.agent.adjust_die_to_other(die_to_adjust)

            powers_triggered = [die for die in self.available_dice if die.power_triggered]
            print(f'Rolled Dice: {self.available_dice}')

    def get_active_tiles(self, game: Game):
        return [tile for tile in self.tiles if tile.ability.activation is not None and not tile.disabled and self.step in tile.ability.activation_window and tile.ability.activation_restriction(self, game)]

    def query_optional_activations(self, game: Game):
        for tile in self.get_active_tiles(game):
            print(f"Activate {tile}?")
            if self.agent.choose_item(["Yes", "No"]) == "Yes":
                assert tile.ability.activation is not None
                tile.activate(self, game)

    def claim_tile(self, game: Game, dice: list[Die], restriction: Callable[[Tile], bool] = lambda t: True):
        self.step = TurnStep.CLAIM
        dice_values = [to_value(die.face) for die in dice if to_value(die.face) != DiceValue.NULL]
        dice_amount = len(dice)
        tile_options: list[Tile] = []
        for tile, condition in game.get_tiles_conditions():
            if tile not in self.tiles and game.tile_available(tile) and dice_amount >= tile.level and condition.function(dice_values) and restriction(tile):
                print(f"{self.agent}'s dice fulfill the {condition} condition for the {tile} tile.")
                tile_options.append(tile)
        if tile_options:
            tile_to_claim = self.agent.choose_item(tile_options)
            game.claim_tile(self, tile_to_claim)
            print(f"{tile_to_claim} claimed by {self.agent}!")
            self.query_optional_activations(game)
        else:
            print(f"{self.agent} couldn't claim any tiles! They recieved 2 tokens as compensation.")
            self.add_scarabs(2)

    def take_turn(self, game: Game):
        # Reset Dice Zones
        self.available_dice = []
        self.locked_dice = []
        self.prepared_dice = []

        # Turn Start
        print(f"===={self.agent}'s turn!====")
        self.step = TurnStep.TURN_START
        for tile in self.tiles:
            if tile.type in [TileType.YELLOW, TileType.BLUE]:
                tile.disabled = False
            if tile.ability.turn_start is not None:
                tile.ability.turn_start(self, game, tile)
                tile.value = 0
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

                game.print_tiles()
                print(f'Rolled Dice: {self.available_dice}')
                print(f'Locked dice: {self.locked_dice}')
                print(
                    f'Tokens: {FOREGROUND(pipup_color)}{self.pip_up_amount} Pip-ups{RESET}, {FOREGROUND(reroll_color)}{self.reroll_amount} Rerolls{RESET}')
                print(f"Tiles: {self.tiles}")

                self.powers_rolled = [die.face for die in self.available_dice if die.face in Die.power_faces]
                self.resolve_powers_rolled(game)

                print("\nAvailable actions:")
                for i, action in enumerate(actions):
                    print(f"{i + 1}. {action.name}")

                choice = "lock"
                if actions:
                    choice = input("Choose an action by number or name (or 'lock'): ").strip().lower()

                if choice == "lock":
                    self.step = TurnStep.LOCK
                    dice_to_lock = self.agent.choose_dice(self, game, 0, maximum=None, message="Choose Dice to Lock")
                    dice_to_reroll = [die for die in self.available_dice if die not in dice_to_lock]
                    if any(die.dice_type == DiceType.IMMEDIATE for die in dice_to_reroll):
                        print("Immediate Dice must be locked.")
                        continue
                    if not dice_to_lock:
                        if not self.available_dice:
                            break
                        print("Dice Locking cancelled.")
                        continue
                    self.locked_dice.extend(dice_to_lock)
                    self.prepared_dice.extend(dice_to_reroll)
                    self.available_dice = []

                    self.locked_pair = pair_constraint.function([die.value for die in dice_to_lock if die.value is not DiceValue.NULL])
                    self.query_optional_activations(game)
                    self.locked_pair = False
                    break

                selected_action = None

                if choice.isdigit():
                    index = int(choice) - 1
                    if 0 <= index < len(actions):
                        selected_action = actions[index]
                    else:
                        print("Invalid number. Try again.")
                        continue
                else:
                    for action in actions:
                        if action.name.lower() == choice:
                            selected_action = action
                            break
                    if not selected_action:
                        print("Invalid name. Try again.")
                        continue

                print(f"You chose: {selected_action.name}")

                try:
                    selected_action.function(self, game)
                    self.resolve_powers_rolled(game)
                except SelectionException as e:
                    print(e.args)
                except PipUpException:
                    print("Can't pip-up that die!")
                except RearrangementException:
                    print("Rearrangement Failed!")
        # Claim Phase

        print(f"{self.agent} finished their roll with {self.locked_dice} locked.")
        self.claim_tile(game, self.locked_dice)
        self.step = TurnStep.CLAIM_END
        self.query_optional_activations(game)

        print(f"====End of {self.agent}'s turn!====")
        self.step = TurnStep.NONE
