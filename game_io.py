
from __future__ import annotations
from dataclasses import dataclass
import itertools
from typing import Any, Protocol, TYPE_CHECKING, TypeVar

import pygame

from dice import Die
from display import BOLD, FOREGROUND, RESET, Text_Canvas
from enums import Alert, DiceFace, DiceValue, TileType
from layout_division import FlowDirection, LayoutDivision, Spacing, TextDivision, TextStyle
from tile import SelectionException

if TYPE_CHECKING:
    from player import DiceConstraint
    from main import Game
    from player import Player

T = TypeVar('T')


class IOPort(Protocol):
    def show_board(self, game: Game): ...
    def show_player_state(self, player: Player, game: Game): ...
    def show_message(self, text: str): ...
    def choose_die(self, dice: list[Die], message: str = "Choose a die:", constraint: DiceConstraint = lambda d: True) -> Die: ...
    def choose_dice(self, dice: list[Die], minimum: int, maximum: int | None = -1,
                    message: str = "Choose dice:", constraint: DiceConstraint = lambda d: True) -> list[Die]: ...

    def choose_item(self, prompt: str, options: list[T]) -> T: ...
    def choose_items(self, prompt: str, options: list[T], min_amount: int, max_amount: int | None = -1) -> list[T]: ...
    def choose_rearrangement(self, dice: list[Die], target_sum: int) -> list[tuple[Die, DiceFace]]: ...
    def choose_adjust_face(self, die_to_adjust: Die) -> DiceFace: ...
    def alert(self, event: Alert, data: dict[str, Any] = {}): ...


class ConsoleIO(IOPort):
    def show_board(self, game: Game):
        canvas_width = 180
        canvas_height = 60
        canvas = Text_Canvas(canvas_width, canvas_height)
        '''
        White 255\n
        Red 196\n
        Blue 21\n
        Green 76\n
        Black 234\n
        Gold 220\n
        Gray 110\n
        '''
        color_dict = {TileType.YELLOW: 220, TileType.BLUE: 21, TileType.RED: 196}
        # Layout settings
        tile_width = 37
        tile_height = 7
        x_margin = 2
        y_margin = 3

        left_buffer = 2

        for level, tile_list in game.tiles.items():
            if level > 1:
                x = x_margin + 4 * (tile_width + x_margin)+left_buffer
                y = y_margin + (7-level) * (tile_height + y_margin)
                canvas.draw_text(x + 1, y-2, f"{game.get_row_mode(level).name} side", fcolor=7, bcolor=0)
            for index, tile in enumerate(tile_list):
                row = max(2, level)
                x = x_margin + index * (tile_width + x_margin)+left_buffer
                y = y_margin + (7-row) * (tile_height + y_margin)

                # Draw background rectangle for the tile
                canvas.draw_rect(x, y, tile_width, tile_height, color=234)
                canvas.draw_rect(x+1, y+1, tile_width-2, tile_height-2, color=color_dict[tile.type])

                # Get tile description (you might want to use tile.name or str(tile))
                tile_text = tile.name

                # Get condition
                condition = game.get_condition(level, index)

                # Write tile text and condition
                canvas.draw_text(x, y - 2, condition.name.center(tile_width), fcolor=7, bcolor=color_dict[tile.type])
                if not game.amounts[tile]:
                    continue
                canvas.draw_text(x, y, f"x{game.amounts[tile]} ".rjust(tile_width), fcolor=7, bcolor=0)
                canvas.draw_text(x + 1, y, tile_text, fcolor=7, bcolor=0)

                def split_string_by_length(text: str, length: int):
                    return [text[i:i+length] for i in range(0, len(text), length)]
                for i, row in enumerate(split_string_by_length(tile.description, tile_width-2)):
                    canvas.draw_text(x + 1, y+1+i, row, fcolor=7, bcolor=color_dict[tile.type])
            canvas.display()

    def show_player_state(self, player: Player, game: Game):
        pipup_color = 5
        reroll_color = 2
        print(f"===={player}'s {"turn" if not game.final_roll_off else "final roll"}!====")
        print(f'Rolled Dice: {player.available_dice}')
        print(f'Locked dice: {player.locked_dice}')
        print(f'Rolled Dice: {player.available_dice}')
        print(f'Locked dice: {player.locked_dice}')
        print(
            f'Tokens: {FOREGROUND(pipup_color)}{player.pip_up_amount} Pip-ups{RESET}, {FOREGROUND(reroll_color)}{player.reroll_amount} Rerolls{RESET}')
        print(f"Tiles: {player.tiles}")

    def show_message(self, text: str):
        print(text)

    def choose_die(self, dice: list[Die], message: str = "Choose a die:", constraint: DiceConstraint = lambda d: True) -> Die:
        return self.choose_dice(dice, minimum=1, message=message)[0]

    def choose_dice(self, dice: list[Die], minimum: int, maximum: int | None = -1, message: str = "Choose dice:", constraint: DiceConstraint = lambda d: True) -> list[Die]:
        dice = [die for die in dice if constraint(die)]
        if minimum > len(dice):
            raise SelectionException(f"Cannot choose {minimum} dice from only {len(dice)} available.")

        if maximum is None:
            maximum = len(dice)

        print(message)
        for idx, die in enumerate(dice):
            print(f"{idx + 1}: {die}")

        while True:
            amount_str = str(minimum)
            if maximum > minimum:
                amount_str = f'{minimum} to {maximum}'
            raw_input = input(f"Enter {amount_str} distinct dice numbers, separated by commas: ")
            if minimum == 0 and raw_input.lower() == "none":
                return []
            if maximum >= len(dice) and raw_input.lower() == "all":
                return dice
            try:
                selections = [int(x.strip()) for x in raw_input.split(',')]
            except ValueError:
                print("Please enter only numbers separated by commas.")
                continue

            if len(selections) != minimum and maximum <= minimum:
                print(f"Please select exactly {minimum} dice.")
                continue

            if len(selections) < minimum and maximum > minimum:
                print(f"Please select between {minimum} and {maximum} dice.")
                continue

            if len(set(selections)) != len(selections):
                print("Duplicate selections detected. All choices must be distinct.")
                continue

            if any(choice < 1 or choice > len(dice) for choice in selections):
                print("One or more choices are out of valid range.")
                continue

            chosen_dice = [dice[i - 1] for i in selections]
            return chosen_dice

    def choose_item(self, prompt: str, options: list[T]) -> T:
        return self.choose_items(prompt, options, min_amount=1)[0]

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

    def choose_rearrangement(self, dice: list[Die], target_sum: int) -> list[tuple[Die, DiceFace]]:
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

    def choose_adjust_face(self, die_to_adjust: Die) -> DiceFace:
        face_options = sorted(die_to_adjust.faces, key=lambda f: f.value)
        face_options.remove(die_to_adjust.face)
        new_face = self.choose_item("Choose a new face:", face_options)
        return new_face

    def alert(self, event: Alert, data: dict[str, Any] = {}):
        match event:
            case Alert.ROLL_OFF:
                print("The Final Roll-Off has begun!")
            case Alert.SCORE_SUBMITTED:
                player: Player = data['player']
                pharaoh_taken: bool = data['pharaoh-taken']
                print(f"{player} has submitted a score of {player.final_score[0]} {DiceValue(player.final_score[1]).name}s!")
                if pharaoh_taken:
                    print(f"{player} takes the Pharaoh!")
                else:
                    print(f"{player} does not take the Pharaoh...")
            case Alert.GAME_BEGIN:
                print(BOLD+"Welcome to Favor of the Pharaoh!"+RESET)
                print("================================")
            case Alert.GAME_END:
                print("================================")
                print(BOLD+"Game Over!"+RESET)
                print("================================")
                players: list[Player] = data['players']
                winner: Player | None = data['winner']
                for player in players:
                    print(f"{player} scored {player.final_score[0]} {DiceValue(player.final_score[1]).name}s.")
                if winner is not None:
                    print(f"{winner} wins!")
                else:
                    print("Nobody wins!")


@dataclass
class LayoutState():
    conditions: dict[int, list[str]]
    tile_names: dict[int, list[str]]
    tile_descriptions: dict[int, list[str]]
    tile_counts: dict[int, list[int]]
    sides: dict[int, str]

    def get_condition(self, x: int, y: int):
        return self.conditions[y][x]

    def get_tile_name(self, x: int, y: int):
        return self.tile_names[y][x]

    def get_tile_description(self, x: int, y: int):
        return self.tile_descriptions[y][x]

    def get_tile_count(self, x: int, y: int):
        return self.tile_counts[y][x]

    def get_side(self, y: int):
        return self.sides[y]

    def add_herder(self, tile_description: str, tile_count: int):
        self.conditions[1] = ["Any Roll"]
        self.tile_names[1] = ["Herder"]
        self.tile_descriptions[1] = [tile_description]
        self.tile_counts[1] = [tile_count]


class DisplayException(Exception):
    pass


class PygameIO(IOPort):
    def _generate_layout(self):
        # Color definitions
        COLOR_DICT: dict[TileType | str, tuple[int, int, int]] = {
            TileType.YELLOW: (255, 215, 0),
            TileType.BLUE: (0, 102, 204),
            TileType.RED: (220, 20, 60),
            "background": (30, 30, 30),
            "tile_bg": (60, 60, 60),
            "text": (255, 255, 255),
            "text-dark": (30, 30, 30),
            "gray": (180, 180, 180),
        }

        # Font definitions
        FONT_DICT: dict[str, TextStyle] = {
            "title": TextStyle((255, 255, 255), "consolas", 18),
            "title-dark": TextStyle((30, 30, 30), "consolas", 18),
            "side": TextStyle((255, 255, 255), "consolas", 20),
            "description": TextStyle((255, 255, 255), "consolas", 15),
            "description-dark": TextStyle((30, 30, 30), "consolas", 15),
            "condition": TextStyle((255, 255, 255), "consolas", 16, is_bold=True),
        }

        def get_tile_type(x: int):
            match x:
                case 0 | 1:
                    return TileType.YELLOW
                case 2:
                    return TileType.BLUE
                case 3:
                    return TileType.RED
                case _:
                    raise ValueError(f"Undefined column value: {x}")

        def create_tile(x: int, y: int):
            return LayoutDivision(
                margin=Spacing.all(10),
                padding=Spacing.all(5),
                background_color=COLOR_DICT["tile_bg"],
                horiz_alignment=0.5,
                children=[
                    TextDivision(
                        text_callback=lambda: self.layout_state.get_condition(x, y),
                        text_style=FONT_DICT["condition"],
                        flex=1,
                        flex_weight=1,
                        vert_alignment=0.5,
                        horiz_alignment=0.5

                    ),
                    LayoutDivision(
                        background_color=COLOR_DICT[get_tile_type(x)],
                        padding=Spacing.all(5),
                        flex_weight=5,
                        children=[
                            LayoutDivision(
                                children=[
                                    TextDivision(
                                        text_callback=lambda: self.layout_state.get_tile_name(x, y),
                                        text_style=FONT_DICT["title" if get_tile_type(
                                            x) is not TileType.YELLOW else "title-dark"],
                                        flex=1,
                                        horiz_alignment=0
                                    ),
                                    TextDivision(
                                        text_callback=lambda: f"x{self.layout_state.get_tile_count(x, y)}",
                                        text_style=FONT_DICT["title" if get_tile_type(
                                            x) is not TileType.YELLOW else "title-dark"],
                                        flex=1,
                                        horiz_alignment=1
                                    ),
                                ],
                                flow_direction=FlowDirection.RIGHT
                            ),
                            TextDivision(
                                text_callback=lambda: self.layout_state.get_tile_description(x, y),
                                text_style=FONT_DICT["description" if get_tile_type(
                                    x) is not TileType.YELLOW else "description-dark"],
                                margin=Spacing.all(5),
                                flex=1,
                                flex_weight=4
                            )
                        ]
                    )
                ]
            )
        layout = LayoutDivision(
            # padding=Spacing.axis(horiz=10),
            background_color=COLOR_DICT["background"],
            children=[

                LayoutDivision(
                    # margin=Spacing.axis(vert=5),
                    # padding=Spacing.all(5),
                    # background_color=(255, 0, 0),
                    children=[
                        create_tile(x, y)
                        for x in range(4)
                    ] + [
                        TextDivision(
                            text_callback=lambda y=y: self.layout_state.get_side(y),
                            text_style=FONT_DICT["side"],
                            margin=Spacing.all(10),
                            padding=Spacing.all(5)
                        )
                    ],
                    flow_direction=FlowDirection.RIGHT
                )
                for y in range(7, 2, -1)
            ] + [
                LayoutDivision(
                    children=[
                        create_tile(0, 1),
                        LayoutDivision(flex_weight=4)
                    ],
                    flow_direction=FlowDirection.RIGHT
                )

            ]
        )

        return layout

    def __init__(self) -> None:
        SCREEN_WIDTH = 1500
        SCREEN_HEIGHT = 1000
        self.running = True
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        self.layout_state = LayoutState(conditions={},
                                        tile_names={},
                                        tile_descriptions={},
                                        tile_counts={},
                                        sides={},
                                        )
        self.layout = self._generate_layout()
        self.events: list[pygame.event.Event] = []

    def _process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.events.append(event)

    def _get_events(self):
        self._process_events()
        events = self.events
        self.events = []
        return events

    def _render(self):
        if not self.running:
            raise DisplayException("Display has stopped!")
        screen_w, screen_h = self.screen.get_size()
        layout_surface = self.layout.draw((screen_w, (screen_h*2)//3))
        self.screen.blit(layout_surface, (0, 0))
        pygame.display.flip()

    def show_board(self, game: Game):
        self.layout_state.conditions = {lvl: [game.get_condition(lvl, x).name for x in range(4)] for lvl in range(7, 2, -1)}
        self.layout_state.tile_names = {lvl: [game.tiles[lvl][x].name for x in range(4)] for lvl in range(7, 2, -1)}
        self.layout_state.tile_descriptions = {lvl: [game.tiles[lvl][x].description for x in range(4)] for lvl in range(7, 2, -1)}
        self.layout_state.tile_counts = {lvl: [game.get_tile_amount(game.tiles[lvl][x]) for x in range(4)] for lvl in range(7, 2, -1)}
        self.layout_state.sides = {lvl: f'{game.get_row_mode(lvl).name} side' for lvl in range(7, 2, -1)}

        herder = game.tiles[1][0]
        self.layout_state.add_herder(herder.description, game.get_tile_amount(herder))

    def show_player_state(self, player: Player, game: Game):
        self.show_board(game)
        ...

    def show_message(self, text: str): ...

    def choose_die(self, dice: list[Die], message: str = "Choose a die:", constraint: DiceConstraint = lambda d: True) -> Die:
        while True:
            for _event in self._get_events():
                ...
            self._render()
            self.clock.tick(30)

    def choose_dice(self, dice: list[Die], minimum: int, maximum: int | None = -1,
                    message: str = "Choose dice:", constraint: DiceConstraint = lambda d: True) -> list[Die]:
        while True:
            for _event in self._get_events():
                ...
            self._render()
            self.clock.tick(30)

    def choose_item(self, prompt: str, options: list[T]) -> T:
        while True:
            for _event in self._get_events():
                ...
            self._render()
            self.clock.tick(30)

    def choose_items(self, prompt: str, options: list[T], min_amount: int, max_amount: int | None = -1) -> list[T]:
        while True:
            for _event in self._get_events():
                ...
            self._render()
            self.clock.tick(30)

    def choose_rearrangement(self, dice: list[Die], target_sum: int) -> list[tuple[Die, DiceFace]]:
        while True:
            for _event in self._get_events():
                ...
            self._render()
            self.clock.tick(30)

    def choose_adjust_face(self, die_to_adjust: Die) -> DiceFace:
        while True:
            for _event in self._get_events():
                ...
            self._render()
            self.clock.tick(30)

    def alert(self, event: Alert, data: dict[str, Any] = {}):
        if event == Alert.ROLL_OFF:
            self.show_message("The Final Roll-Off has begun!")
        elif event == Alert.SCORE_SUBMITTED:
            player = data['player']
            pharaoh_taken = data['pharaoh-taken']
            msg = f"{player} has submitted a score of {player.final_score[0]} {DiceValue(player.final_score[1]).name}s!"
            if pharaoh_taken:
                msg += f" {player} takes the Pharaoh!"
            else:
                msg += f" {player} does not take the Pharaoh..."
            self.show_message(msg)
        elif event == Alert.GAME_BEGIN:
            self.show_message("Welcome to Favor of the Pharaoh!")
        elif event == Alert.GAME_END:
            players = data['players']
            winner = data['winner']
            msg = "Game Over!\n"
            for player in players:
                msg += f"{player} scored {player.final_score[0]} {DiceValue(player.final_score[1]).name}s.\n"
            if winner is not None:
                msg += f"{winner} wins!"
            else:
                msg += "Nobody wins!"
            self.show_message(msg)
