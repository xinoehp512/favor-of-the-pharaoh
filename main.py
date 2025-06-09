
import random

from tile import *
from enums import *
from constraint import a_rows, b_rows


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


tiles = [farmer, guard, indentured_worker, serf, worker, beggar, servant, soothsayer, ankh, omen, ancestral_guidance, artisan, builder, noble_adoption, palace_servants, soldier, grain_merchant, entertainer, matchmaker, good_omen, palace_key, spirit_of_the_dead, charioteer, conspirator, overseer, ship_captain, tomb_builder, head_servant,
         master_artisan, priest, bad_omen, burial_mask, royal_decree, embalmer, estate_overseer, grain_trader, priest_of_the_dead, royal_attendents, astrologer, priestess, surveyor, pharaohs_gift, secret_passage, treasure, general, grand_vizier, granary_master, heir, royal_astrologer, royal_mother, queens_favor, royal_death, royal_power]
tile_set = TileSet(tiles)


def main():
    # with open("input.txt") as in_file, open("output.txt", "w") as out_file:
    #     tiletypes = {"y": "YELLOW", "b": "BLUE", "r": "RED"}
    #     for line in in_file:
    #         name, level, type = line.rstrip().split(" ")
    #         out_file.write(
    #             f'{name.replace("-", "_").replace("'", "")} = Tile("{name.replace("-", " ").upper()}", {level}, TileType.{tiletypes[type]})\n')

    # game = Game([], None)
    # game.print_tiles()
    rolls: list[list[DiceValue]] = []
    for __ in range(10):
        rolls.append([random.choice(list(DiceValue)) for _ in range(10)])
    for row in a_rows+b_rows:
        for constraint in row:
            for roll in rolls:
                if constraint.function(roll):
                    print(constraint.name, "".join(sorted(str(face.value) for face in roll)), constraint.function(roll))


if __name__ == "__main__":
    main()
