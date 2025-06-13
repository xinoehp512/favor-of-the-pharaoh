
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

    def get_row_mode(self, level: int):
        return self.modes[level-3]

    def get_condition(self, level: int, idx: int):
        if level == 1:
            return any_roll_constraint
        if self.get_row_mode(level) == RowMode.A:
            return a_rows[level-3][idx]
        else:
            return b_rows[level-3][idx]

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
        if tile in player.tiles:
            raise Exception("Players may only have one of each tile.")
        if self.amounts[tile] == 0:
            raise Exception(f"All {tile}s have been claimed.")
        self.amounts[tile] -= 1
        player.tiles.append(tile)
        if tile.type == TileType.BLUE:
            player.add_scarabs(1)
        if tile.type == TileType.RED:
            player.add_scarabs(2)
        if tile.ability.on_claim is not None:
            tile.ability.on_claim(player, self, tile)

    def set_next_turn(self, player: Player):
        self.next_player_turn = self.players.index(player)

    def play_game(self):
        print(BOLD+"Welcome to Favor of the Pharaoh!"+RESET)
        print("================================")
        while True:
            next_player = self.players[self.next_player_turn]
            self.next_player_turn += 1
            self.next_player_turn %= len(self.players)
            next_player.take_turn(self)


tile_set = TileSet(tiles)


def main():
    player = Player([start, palace_servants, serf, artisan, conspirator, ship_captain, noble_adoption,
                    grand_vizier, royal_astrologer], Agent("Player 1", 4), starting_tokens=10)
    player2 = Player([start], Agent("Player 2", 1), starting_tokens=10)
    game = Game([player, player2])
    random.seed(1)
    game.play_game()
    # print(game.get_tiles_conditions())


if __name__ == "__main__":
    main()
