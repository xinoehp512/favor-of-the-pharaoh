from __future__ import annotations
from collections.abc import Callable
import random
from dice import Die, PipUpException
from display import COLOR, FOREGROUND, RESET
from enums import *
from tile import Tile


from typing import TYPE_CHECKING, List, TypeVar
if TYPE_CHECKING:
    from main import Game

ActionFunction = Callable[['Player', 'Game'], None]


class Action:
    def __init__(self, name: str, func: ActionFunction) -> None:
        self.name = name
        self.function = func


def pipup_function(player: Player, game: Game):
    if ScarabType.PIPUP not in player.tokens:
        raise Exception("No pip-up scarab!")
    player.agent.choose_dice(player, game, 1, message="Choose die to pipup:")[0].pipup()
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


class Agent:
    def __init__(self, name: str, color: int) -> None:
        self.name = name
        self.color = color

    def choose_dice(self, player: Player, game: Game, amount: int, maximum: int | None = -1, message: str = "Choose dice:") -> list[Die]:
        available_dice = player.available_dice

        if amount > len(available_dice):
            raise ValueError(f"Cannot choose {amount} dice from only {len(available_dice)} available.")

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

    def choose_item(self, options: List[T], display: Callable[[T], str] = str) -> T:
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
        self.add_scarabs(starting_tokens)

    @property
    def pip_up_amount(self):
        return self.tokens.count(ScarabType.PIPUP)

    @property
    def reroll_amount(self):
        return self.tokens.count(ScarabType.REROLL)

    def add_scarabs(self, amount: int):
        for _ in range(amount):
            self.tokens.append(random.choice([ScarabType.PIPUP, ScarabType.REROLL]))

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
                    face_options = die_to_adjust.faces
                    face_options.remove(die_to_adjust.face)
                    print("Choose a new face:")
                    new_face = self.agent.choose_item(face_options)
                    die_to_adjust.set_face(new_face)

            powers_triggered = [die for die in self.available_dice if die.power_triggered]
            print(f'Rolled Dice: {self.available_dice}')

    def take_turn(self, game: Game):
        # Reset Dice Zones
        self.available_dice = []
        self.locked_dice = []
        self.prepared_dice = []

        # Turn Start
        print(f"===={self.agent}'s turn!====")
        for tile in self.tiles:
            if tile.type in [TileType.YELLOW, TileType.BLUE]:
                tile.disabled = False
            if tile.ability.turn_start is not None:
                tile.ability.turn_start(self, game, tile)
                tile.value = 0
        while self.prepared_dice:
            # Roll
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
                for tile in self.tiles:
                    if tile.ability.activation is not None and not tile.disabled:
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
                    dice_to_lock = self.agent.choose_dice(self, game, 0, maximum=None, message="Choose Dice to Lock")
                    dice_to_reroll = [die for die in self.available_dice if die not in dice_to_lock]
                    if any(die.dice_type == DiceType.IMMEDIATE for die in dice_to_reroll):
                        print("Immediate Dice must be locked.")
                        continue
                    if not dice_to_lock:
                        print("Dice Locking cancelled.")
                        continue
                    self.locked_dice.extend(dice_to_lock)
                    self.prepared_dice.extend(dice_to_reroll)
                    self.available_dice = []
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

                except PipUpException:
                    print("Can't pip-up that die!")
        # Claim Phase
        dice_values = [to_value(die.face) for die in self.locked_dice]
        dice_amount = len(self.locked_dice)
        print(f"{self.agent} finished their roll with {dice_values} locked.")
        tile_options: list[Tile] = []
        for tile, condition in game.get_tiles_conditions():
            if tile not in self.tiles and game.tile_available(tile) and dice_amount >= tile.level and condition.function(dice_values):
                print(f"{self.agent}'s dice fulfill the {condition} condition for the {tile} tile.")
                tile_options.append(tile)
        if tile_options:
            tile_to_claim = self.agent.choose_item(tile_options)
            game.claim_tile(self, tile_to_claim)
            print(f"{tile_to_claim} claimed by {self.agent}!")
        else:
            print(f"{self.agent} couldn't claim any tiles! They recieved 2 tokens as compensation.")
            self.add_scarabs(2)

        print(f"====End of {self.agent}'s turn!====")
