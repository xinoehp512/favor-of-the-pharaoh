
import random

from display import BOLD, RESET
from tile import *
from enums import *
from constraint import Constraint, a_rows, b_rows, any_roll_constraint
from player import Agent, Player


class TileSet:
    def __init__(self, tiles: list[Tile]) -> None:
        self.tiles = tiles

    def get_category(self, level: int, type: TileType):
        return [tile for tile in self.tiles if tile.level == level and tile.type == type]


class Game:
    def __init__(self, players: list[Player], modes: list[RowMode] | None = None, tiles: list[Tile] | None = None, ) -> None:
        self.modes = modes or [random.choice([RowMode.A, RowMode.B]) for _ in range(5)]
        self.players = players
        self.tiles: dict[int, list[Tile]] = {}

        self.final_roll_off = False
        self.high_score = (7, 0)
        self.high_scorer: Player | None = None

        self.next_player_turn = 0

        if tiles is None:
            for level in range(3, 8):
                yellows = random.sample(tile_set.get_category(level, TileType.YELLOW), 2) if level != 7 else [
                    queen]+random.sample(tile_set.get_category(level, TileType.YELLOW), 1)
                blue = random.sample(tile_set.get_category(level, TileType.BLUE), 1)
                red = random.sample(tile_set.get_category(level, TileType.RED), 1)
                self.tiles[level] = yellows+blue+red
        else:
            for level in range(3, 8):
                yellows = ([] if level != 7 else [queen]) + [tile for tile in tiles if tile.level == level and tile.type == TileType.YELLOW]
                blue = [tile for tile in tiles if tile.level == level and tile.type == TileType.BLUE]
                red = [tile for tile in tiles if tile.level == level and tile.type == TileType.RED]
                if len(yellows+blue+red) != 4:
                    raise Exception(f"Incorrect tile setup: length of {yellows+blue+red} is not 4.")
                self.tiles[level] = yellows+blue+red
        self.tiles[1] = [herder]

        self.amounts: dict[Tile, int] = {}
        player_count = len(self.players)
        amount_by_level = {
            1: player_count,
            3: player_count,
            4: max(1, player_count-1),
            5: max(1, player_count-2),
            6: max(1, player_count-2),
            7: 1
        }
        for level, tiles in self.tiles.items():
            for tile in tiles:
                self.amounts[tile] = amount_by_level[level]

    @property
    def game_ended(self):
        return all(player.finished for player in self.players)

    def get_opponents(self, player: Player):
        return [p for p in self.players if p != player]

    def get_row_mode(self, level: int):
        return self.modes[level-3]

    def get_condition(self, level: int, idx: int):
        if level == 1:
            return any_roll_constraint
        if self.get_row_mode(level) == RowMode.A:
            return a_rows[level-3][idx]
        else:
            return b_rows[level-3][idx]

    def get_all_tiles(self):
        return [tile for row in self.tiles.values() for tile in row]

    def get_available_tiles(self, player: Player, condition: Callable[[Tile], bool]) -> list[Tile]:
        return [tile for tile in self.get_all_tiles() if tile not in player.tiles and self.tile_available(tile) and condition(tile)]

    def print_tiles(self):
        for level in range(7, 2, -1):
            print(f"Level {level} Tiles ({self.get_row_mode(level).name} side): {self.tiles[level]}")

    def get_tiles_conditions(self):
        tiles_and_conditions: list[tuple[Tile, Constraint]] = []
        for level, tiles in self.tiles.items():
            for idx, tile in enumerate(tiles):
                tiles_and_conditions.append((tile, self.get_condition(level, idx)))
        return tiles_and_conditions

    def tile_available(self, tile: Tile):
        return self.amounts[tile] > 0

    def claim_tile(self, player: Player, tile: Tile):
        if self.final_roll_off:
            print("Players cannot claim tiles during the final roll-off.")
            return
        if tile in player.tiles:
            raise Exception("Players may only have one of each tile.")
        if self.amounts[tile] == 0:
            raise Exception(f"All {tile}s have been claimed.")
        self.amounts[tile] -= 1
        player.tiles.append(tile.clone())
        print(f"{tile} claimed by {player}!")
        if tile.type == TileType.BLUE:
            player.add_scarabs(1)
        if tile.type == TileType.RED:
            player.add_scarabs(2)
        if tile.ability.on_claim is not None:
            tile.ability.on_claim(player, self, tile)

    def set_next_turn(self, player: Player):
        self.next_player_turn = self.players.index(player)

    def begin_final_roll_off(self):
        def add_red(player: Player, game: Game):
            player.prepared_dice.append(get_die(DiceType.STANDARD))
        self.final_roll_off = True
        for i in range(self.next_player_turn, len(self.players)):
            self.players[i].add_effect(Effect(add_red))
        print("The Final Roll-Off has begun!")

    def submit_score(self, player: Player):
        if player.final_score == (0, 0):
            return
        print(f"{player} has submitted a score of {player.final_score[0]} {DiceValue(player.final_score[1]).name}s!")
        if player.final_score > self.high_score:
            self.high_scorer = player
            self.high_score = player.final_score
            print(f"{player} takes the Pharaoh!")
        else:
            print(f"{player} does not take the Pharaoh...")

    def play_game(self):
        print(BOLD+"Welcome to Favor of the Pharaoh!"+RESET)
        print("================================")
        while not self.game_ended:
            next_player = self.players[self.next_player_turn]
            self.next_player_turn += 1
            self.next_player_turn %= len(self.players)
            next_player.take_turn(self)
        print("================================")
        print(BOLD+"Game Over!"+RESET)
        print("================================")
        for player in self.players:
            print(f"{player} scored {player.final_score[0]} {DiceValue(player.final_score[1]).name}s.")
        if self.high_scorer is not None:
            print(f"{self.high_scorer} wins!")
        else:
            print("Nobody wins!")


tile_set = TileSet(tiles)


def main():
    player = Player([tile.clone() for tile in [start, grand_vizier, master_artisan]], Agent("Player 1", 4), starting_tokens=0)
    player2 = Player([start, indentured_worker, builder, royal_attendants, royal_decree, pharaohs_gift,
                     surveyor, royal_mother], Agent("Player 2", 1), starting_tokens=1)
    random.seed(1)
    game = Game([player, player2])
    game.play_game()
    # print(game.get_tiles_conditions())


if __name__ == "__main__":
    main()
