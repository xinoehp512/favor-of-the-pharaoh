

import itertools
from typing import Any, Protocol, TYPE_CHECKING, TypeVar

from dice import Die
from display import BOLD, FOREGROUND, RESET, Text_Canvas
from enums import Alert, DiceFace, DiceValue, TileType
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
