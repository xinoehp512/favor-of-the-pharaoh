
import random

from tile import *
from enums import *
from constraint import a_rows, b_rows  # type: ignore
from player import Agent, Player


class TileSet:
    def __init__(self, tiles: list[Tile]) -> None:
        self.tiles = tiles

    def get_category(self, level: int, type: TileType):
        return [tile for tile in self.tiles if tile.level == level and tile.type == type]


class Game:
    def __init__(self, modes: list[RowMode], tiles: list[Tile] | None = None) -> None:
        self.modes = modes
        self.tiles: dict[int, list[Tile]] = {}
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

    def get_row_mode(self, level: int):
        return self.modes[level-3]

    def print_tiles(self):
        for level, tiles in self.tiles.items():
            print(f"Level {level} Tiles: {tiles}")


tile_set = TileSet(tiles)


def main():
    player = Player([start, estate_overseer, granary_master], Agent("Player 1"))
    game = Game([], None)
    player.take_turn(game)


if __name__ == "__main__":
    main()
