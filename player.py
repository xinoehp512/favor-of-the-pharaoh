from __future__ import annotations
from collections.abc import Callable
import random
from dice import Die, PipUpException
from enums import *
from tile import Tile


from typing import TYPE_CHECKING
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
    player.agent.choose_dice(player, game, 1, "Choose die to pipup:")[0].pipup()
    player.tokens.remove(ScarabType.PIPUP)


def reroll_function(player: Player, game: Game):
    if ScarabType.REROLL not in player.tokens:
        raise Exception("No reroll scarab!")
    player.agent.choose_dice(player, game, 1, "Choose die to reroll:")[0].roll()
    player.tokens.remove(ScarabType.REROLL)


pipup_action = Action("Use Pip-up Token", pipup_function)
reroll_action = Action("Use Reroll Token", reroll_function)


class Agent:
    def __init__(self, name: str) -> None:
        self.name = name

    def choose_dice(self, player: Player, game: Game, amount: int, message: str = "Choose dice:"):
        available_dice = player.available_dice

        if amount > len(available_dice):
            raise ValueError(f"Cannot choose {amount} dice from only {len(available_dice)} available.")

        print(message)
        for idx, die in enumerate(available_dice):
            print(f"{idx + 1}: {die}")

        while True:
            raw_input = input(f"Enter {amount} distinct dice numbers (1-{len(available_dice)}), separated by commas: ")
            try:
                selections = [int(x.strip()) for x in raw_input.split(',')]
            except ValueError:
                print("Please enter only numbers separated by commas.")
                continue

            if len(selections) != amount:
                print(f"Please select exactly {amount} dice.")
                continue

            if len(set(selections)) != amount:
                print("Duplicate selections detected. All choices must be distinct.")
                continue

            if any(choice < 1 or choice > len(available_dice) for choice in selections):
                print("One or more choices are out of valid range.")
                continue

            chosen_dice = [available_dice[i - 1] for i in selections]
            return chosen_dice


class Player:
    def __init__(self, tiles: list[Tile], agent: Agent, starting_tokens: int = 0) -> None:
        self.tiles = tiles
        self.agent = agent
        self.available_dice: list[Die] = []
        self.locked_dice: list[Die] = []
        self.prepared_dice: list[Die] = []
        self.tokens: list[ScarabType] = []
        self.add_scarabs(starting_tokens)

    def add_scarabs(self, amount: int):
        for _ in range(amount):
            self.tokens.append(random.choice([ScarabType.PIPUP, ScarabType.REROLL]))

    def take_turn(self, game: Game):
        # Reset Dice Zones
        self.available_dice = []
        self.locked_dice = []
        self.prepared_dice = []

        # Turn Start
        for tile in self.tiles:
            if tile.type in [TileType.YELLOW, TileType.BLUE]:
                tile.disabled = False
            if tile.ability.turn_start is not None:
                tile.ability.turn_start(self, game, tile)
        # print(self.prepared_dice)
        # print(self.tokens)

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
                    actions.append(Action(f"Activate {tile.name}", tile.activate))

            print(self.available_dice)
            print(self.tokens)
            print("\nAvailable actions:")
            for i, action in enumerate(actions):
                print(f"{i + 1}. {action.name}")

            if not actions:
                print("No actions left.")
                break

            choice = input("Choose an action by number or name: ").strip().lower()

            if choice == "quit":
                print("Exiting...")
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
            except PipUpException:
                print("Can't pip-up that die!")
