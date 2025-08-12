
import pygame
from tile import Tile, TileType
from enums import RowMode
from constraint import Constraint

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import Game

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
FONT_DICT: dict[str, tuple[str, int]] = {
    "title": ("consolas", 18),
    "side": ("consolas", 20),
    "description": ("consolas", 15),
}


SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 1000
TILE_WIDTH = 315
TILE_HEIGHT = 125
X_MARGIN = 20
Y_MARGIN = 40

DESC_MAX_CHAR_WIDTH = 37
DESC_MAX_LINES = 5


def split_string_by_length(text: str, length: int):
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > length:
            lines.append(current)
            current = word
        else:
            if current:
                current += " "
            current += word
    if current:
        lines.append(current)
    return lines


class PygameDisplay:
    def __init__(self, game: 'Game'):
        pygame.init()
        self.game = game
        self.title_font = pygame.font.SysFont(*FONT_DICT["title"])
        self.description_font = pygame.font.SysFont(*FONT_DICT["description"])
        self.side_font = pygame.font.SysFont(*FONT_DICT["side"])
        self.condition_font = pygame.font.SysFont("consolas", 16, bold=True)
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Favor of the Pharaoh - Board Display")

    def draw_tile(self, x: int, y: int, tile: Tile, amount: int, condition: Constraint, mode: RowMode):
        # Draw tile background
        pygame.draw.rect(self.screen, COLOR_DICT["tile_bg"], (x, y, TILE_WIDTH, TILE_HEIGHT))
        pygame.draw.rect(self.screen, COLOR_DICT[tile.type], (x+4, y+4, TILE_WIDTH-8, TILE_HEIGHT-8))

        # Draw condition bar above the tile
        cond_bar_height = 28
        cond_bar_rect = (x, y - cond_bar_height, TILE_WIDTH, cond_bar_height)
        pygame.draw.rect(self.screen, COLOR_DICT["tile_bg"], cond_bar_rect)
        cond_surf = self.condition_font.render(condition.name, True, COLOR_DICT["text"])
        cond_text_rect = cond_surf.get_rect(center=(x + TILE_WIDTH // 2, y - cond_bar_height // 2))
        self.screen.blit(cond_surf, cond_text_rect)

        text_color = COLOR_DICT["text"] if tile.type is not TileType.YELLOW else COLOR_DICT["text-dark"]
        # Draw tile name
        name_surf = self.title_font.render(tile.name, True, text_color)
        self.screen.blit(name_surf, (x+10, y+8))

        # Draw tile amount
        amount_surf = self.title_font.render(f"x{amount}", True, COLOR_DICT["gray"])
        self.screen.blit(amount_surf, (x+TILE_WIDTH-40, y+8))

        # Draw description (wrapped)
        desc_lines = split_string_by_length(tile.description, DESC_MAX_CHAR_WIDTH)
        for i, line in enumerate(desc_lines[:DESC_MAX_LINES]):
            desc_surf = self.description_font.render(line, True, text_color)
            self.screen.blit(desc_surf, (x+10, y+30+i*18))

    def draw_board(self):
        self.screen.fill(COLOR_DICT["background"])
        left_buffer = 30
        for level, tile_list in self.game.tiles.items():
            if level > 1:
                x = X_MARGIN + 4 * (TILE_WIDTH + X_MARGIN) + left_buffer
                y = Y_MARGIN + (7-level) * (TILE_HEIGHT + Y_MARGIN)
                mode = self.game.get_row_mode(level)
                mode_surf = self.side_font.render(f"{mode.name} side", True, COLOR_DICT["gray"])
                self.screen.blit(mode_surf, (x+10, y))
            for index, tile in enumerate(tile_list):
                row = max(2, level)
                x = X_MARGIN + index * (TILE_WIDTH + X_MARGIN) + left_buffer
                y = Y_MARGIN + (7-row) * (TILE_HEIGHT + Y_MARGIN)
                condition = self.game.get_condition(level, index)
                amount = self.game.amounts[tile]
                if amount == 0:
                    continue
                self.draw_tile(x, y, tile, amount, condition, self.game.get_row_mode(level))
        pygame.display.flip()

    def run(self):
        running = True
        clock = pygame.time.Clock()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self.draw_board()
            clock.tick(30)
        pygame.quit()
