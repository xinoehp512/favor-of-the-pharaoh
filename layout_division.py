from __future__ import annotations
import random
from typing import Callable, Optional
from enum import Enum
import pygame

from enums import TileType
from player import Agent, Player
from tile import *
from main import Game

pygame.init()

# ---------------- Enums ----------------


class FlowDirection(Enum):
    DOWN = "down"
    RIGHT = "right"

# ---------------- Supporting Classes ----------------


class Spacing:
    """Represents spacing around/between layout elements."""

    def __init__(self, top: int = 0, bottom: int = 0, left: int = 0, right: int = 0):
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right

    @classmethod
    def all(cls, value: int):
        return cls(value, value, value, value)

    @classmethod
    def axis(cls, vert: int = 0, horiz: int = 0):
        return cls(top=vert, bottom=vert, left=horiz, right=horiz)

    @property
    def horizontal(self) -> int:
        """Total horizontal spacing (left + right)."""
        return self.left + self.right

    @property
    def vertical(self) -> int:
        """Total vertical spacing (top + bottom)."""
        return self.top + self.bottom


class BorderStyle:
    """Represents the border styling of a layout element."""

    def __init__(self, size: int = 0, color: Optional[tuple[int, int, int]] = None):
        self.size = size
        self.color = color


class Font:
    fonts: dict[tuple[str, int, bool, bool], pygame.font.Font] = {}

    @classmethod
    def get_font(cls,  text_font: str, text_font_size: int, is_bold: bool = False, is_italic: bool = False):
        font_info = (text_font, text_font_size, is_bold, is_italic)
        if font_info in cls.fonts:
            return cls.fonts[font_info]
        else:
            font = pygame.font.SysFont(text_font, text_font_size, is_bold, is_italic)
            cls.fonts[font_info] = font
            return font


class TextStyle:
    """Represents styling for text rendering."""

    def __init__(self, text_color: tuple[int, int, int], text_font: str, text_font_size: int, is_bold: bool = False, is_italic: bool = False):
        self.text_color = text_color
        self.text_font = text_font
        self.text_font_size = text_font_size
        self.is_bold = is_bold
        self.is_italic = is_italic

    def get_font_info(self):
        return (self.text_font, self.text_font_size, self.is_bold, self.is_italic)

    def get_font(self):
        return Font.get_font(*self.get_font_info())

# ---------------- Base Layout Division ----------------


class LayoutDivision:
    """Base class for layout elements."""

    def __init__(
        self,
        margin: Spacing = Spacing(),
        padding: Spacing = Spacing(),
        border: BorderStyle = BorderStyle(),
        children: Optional[list[LayoutDivision]] = None,
        parent: Optional[LayoutDivision] = None,
        flow_direction: FlowDirection = FlowDirection.DOWN,
        vert_alignment: float = 0.0,
        horiz_alignment: float = 0.0,
        width: Optional[int] = None,
        height: Optional[int] = None,
        flex_weight: float = 1.0,
        background_color: Optional[tuple[int, int, int]] = None,
        flex: int = 1
    ):
        self.margin = margin
        self.padding = padding
        self.border = border
        self.children = children or []
        self.parent = parent
        self.flow_direction = flow_direction
        self.vert_alignment = vert_alignment
        self.horiz_alignment = horiz_alignment
        self.width = width
        self.height = height
        self.flex_weight = flex_weight
        self.background_color = background_color
        self.flex = flex

    def get_size(self) -> Optional[tuple[int, int]]:
        """
        Returns the TOTAL bounding box of this division (including margin, border, and padding).
        If flex is 1 or 2 and size depends on children, may return None.
        """
        if self.flex == 0:
            total_width = (self.width or 0) + self.margin.horizontal + \
                self.border.size * 2 + self.padding.horizontal
            total_height = (self.height or 0) + self.margin.vertical + \
                self.border.size * 2 + self.padding.vertical
            return total_width, total_height
        elif self.flex == 1:
            return None

        elif self.flex == 2 or self.flex == 3:
            child_sizes_raw = [child.get_size() for child in self.children]
            child_sizes: list[tuple[int, int]] = [size for size in child_sizes_raw if size is not None]
            if not child_sizes:
                return None
            if self.flow_direction is FlowDirection.DOWN:
                w = max((s[0] for s in child_sizes), default=0)
                h = sum((s[1] for s in child_sizes), 0)
            else:
                w = sum((s[0] for s in child_sizes), 0)
                h = max((s[1] for s in child_sizes), default=0)
            return (
                w + self.margin.horizontal + self.border.size * 2 + self.padding.horizontal,
                h + self.margin.vertical + self.border.size * 2 + self.padding.vertical
            )
        else:
            raise ValueError(f"Invalid flex value: {self.flex}")

    def draw(self, delegated_size: tuple[int, int]) -> pygame.Surface:
        """
        Draws this division and its children to a surface.
        delegated_size: the size passed down from the parent layout.
        """

        size = self.get_size() or delegated_size
        if self.flex == 3:  # TODO: Make flex work with 'None' in either parameter in get_size.
            size = delegated_size

        surface = pygame.Surface(size, pygame.SRCALPHA)
        if self.background_color:
            x, y, w, h = surface.get_rect()
            pygame.draw.rect(surface, self.background_color, (x+self.margin.top, y +
                             self.margin.left, w-self.margin.horizontal, h-self.margin.vertical))

        if self.border.size > 0 and self.border.color:
            x, y, w, h = surface.get_rect()
            pygame.draw.rect(surface, self.border.color, (x+self.margin.top, y+self.margin.left,
                             w-self.margin.horizontal, h-self.margin.vertical), self.border.size)

        content_width = size[0] - self.padding.horizontal - self.border.size * 2 - self.margin.horizontal
        content_height = size[1] - self.padding.vertical - self.border.size * 2 - self.margin.vertical

        # Layout children
        if self.children:
            total_child_size = 0
            flex_allocation = 0
            for child in self.children:
                child_size = child.get_size()
                if child_size is None:
                    flex_allocation += child.flex_weight
                    continue
                if self.flow_direction is FlowDirection.DOWN:
                    total_child_size += child_size[1]
                else:
                    total_child_size += child_size[0]

            offset_x = self.padding.left + self.border.size + self.margin.left
            offset_y = self.padding.top + self.border.size + self.margin.top
            flex_per = 0
            if self.flow_direction is FlowDirection.DOWN:
                remaining_height = max(content_height-total_child_size, 0)
                if flex_allocation == 0:
                    offset_y += int(remaining_height*self.vert_alignment)
                else:
                    flex_per = remaining_height/flex_allocation
            else:
                remaining_width = max(content_width-total_child_size, 0)
                if flex_allocation == 0:
                    offset_x += int(remaining_width*self.horiz_alignment)
                else:
                    flex_per = remaining_width/flex_allocation

            for child in self.children:
                child_size = child.get_size()
                if child_size is None:
                    if self.flow_direction is FlowDirection.DOWN:
                        child_size = (content_width, int(flex_per*child.flex_weight))
                    else:
                        child_size = (int(flex_per*child.flex_weight), content_height)
                if child.flex == 3:
                    if self.flow_direction is FlowDirection.DOWN:
                        child_size = (content_width, child_size[1])
                    else:
                        child_size = (child_size[0], content_height)

                child_surface = child.draw(child_size)

                child_w, child_h = child_size
                if self.flow_direction is FlowDirection.DOWN:
                    extra_width = max(content_width-child_w, 0)
                    surface.blit(child_surface, (offset_x+int(extra_width*self.horiz_alignment), offset_y))
                else:
                    extra_height = max(content_height-child_h, 0)
                    surface.blit(child_surface, (offset_x, offset_y+int(extra_height*self.horiz_alignment)))

                if self.flow_direction is FlowDirection.DOWN:
                    offset_y += child_surface.get_height()
                elif self.flow_direction is FlowDirection.RIGHT:
                    offset_x += child_surface.get_width()

        return surface

# ---------------- Text Division ----------------


class TextDivision(LayoutDivision):
    """Layout division for rendering text."""

    def __init__(
        self,
        text_callback: Callable[[], str],
        text_style: TextStyle,
        **kwargs  # type: ignore
    ):
        super().__init__(**kwargs)  # type: ignore
        self.text_callback = text_callback
        self.text_style = text_style
        self.font = self.text_style.get_font()
        if "flex" not in kwargs:
            self.flex = 0  # Default flex for text

    @property
    def width(self):
        return self.font.size(self.text_callback())[0]

    @width.setter
    def width(self, value: int):
        return

    @property
    def height(self):
        return self.font.size(self.text_callback())[1]

    @height.setter
    def height(self, value: int):
        return

    def draw(self, delegated_size: tuple[int, int]) -> pygame.Surface:
        """Draws the text, word-wrapping and resizing if flex == 1."""
        draw_w, draw_h = self.get_size() or delegated_size
        content_width = draw_w - self.padding.horizontal - self.border.size * 2 - self.margin.horizontal
        content_height = draw_h - self.padding.vertical - self.border.size * 2 - self.margin.vertical

        surface = pygame.Surface((draw_w, draw_h), pygame.SRCALPHA)
        text = self.text_callback()

        # Auto-fit font size for flex=1

        font = self.font
        lines = [text]
        if self.flex == 1:
            font_size = self._find_max_font_size(text, content_width, content_height)
            font = Font.get_font(self.text_style.text_font, font_size, self.text_style.is_bold, self.text_style.is_italic)
            lines = self._word_wrap(text, font, content_width)

        total_height = 0
        for line in lines:
            size = font.size(line)
            total_height += size[1]
        extra_height = content_height-total_height

        y_offset = self.padding.top + self.border.size + self.margin.top + extra_height*self.vert_alignment
        for line in lines:
            rendered = font.render(line, True, self.text_style.text_color)
            extra_width = content_width - rendered.get_width()
            x_offset = self.margin.left+self.border.size+self.padding.left + extra_width*self.horiz_alignment

            surface.blit(rendered, (x_offset, y_offset))
            y_offset += rendered.get_height()

        return surface

    def _word_wrap(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        """Splits text into lines that fit within max_width."""
        words = text.split(" ")
        lines: list[str] = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    def _find_max_font_size(self, text: str, max_width: int, max_height: int) -> int:
        """
        Finds the largest font size that allows the wrapped text
        to fit in max_width and max_height.
        """
        for size in range(self.text_style.text_font_size, 5, -1):
            font = Font.get_font(self.text_style.text_font, size, self.text_style.is_bold, self.text_style.is_italic)
            lines = self._word_wrap(text, font, max_width)
            total_height = sum(font.size(line)[1] for line in lines)
            if total_height <= max_height:
                return size
        return 5  # Fallback minimum size


def create_layout():
    TEXT_STYLES = {
        "condition": TextStyle((255, 255, 255), "Arial", 14),
        "title": TextStyle((255, 255, 0), "Arial", 16),
        "count": TextStyle((0, 255, 0), "Arial", 14),
        "description": TextStyle((200, 200, 200), "Arial", 12),
        "row-mode": TextStyle((255, 128, 0), "Arial", 14)
    }

    # -------------------------
    # Helper text callback
    # -------------------------
    def dummy_text(name: str) -> Callable[[], str]:
        return lambda: name

    # -------------------------
    # Build Layout
    # -------------------------

    # Top-level layout (flows RIGHT)
    root_layout = LayoutDivision(flow_direction=FlowDirection.RIGHT, children=[])

    # First child (LEFT side) — 6 rows
    left_side = LayoutDivision(flow_direction=FlowDirection.DOWN, children=[])

    for row_index in range(6):
        if row_index < 5:
            # Row with 4 cells
            row = LayoutDivision(flow_direction=FlowDirection.RIGHT, children=[])
            for cell_index in range(4):
                # Cell has 2 children
                condition_div = TextDivision(
                    text_callback=dummy_text(f"Condition {row_index}-{cell_index}"),
                    text_style=TEXT_STYLES["condition"]
                )

                right_side_of_cell = LayoutDivision(flow_direction=FlowDirection.DOWN, children=[])

                # First child of right side contains two TextDivisions (title + count) flowing RIGHT
                title_count_container = LayoutDivision(flow_direction=FlowDirection.RIGHT, children=[])
                title_div = TextDivision(
                    text_callback=dummy_text(f"Title {row_index}-{cell_index}"),
                    text_style=TEXT_STYLES["title"]
                )
                count_div = TextDivision(
                    text_callback=dummy_text(f"{row_index * 10 + cell_index}"),
                    text_style=TEXT_STYLES["count"]
                )
                title_count_container.children.extend([title_div, count_div])

                # Second child of right side contains description (flex 1)
                description_container = LayoutDivision(flow_direction=FlowDirection.DOWN, children=[])
                description_div = TextDivision(
                    text_callback=dummy_text(f"Description {row_index}-{cell_index}"),
                    text_style=TEXT_STYLES["description"],
                    flex=1
                )
                description_container.children.append(description_div)

                right_side_of_cell.children.extend([title_count_container, description_container])

                cell = LayoutDivision(flow_direction=FlowDirection.RIGHT, children=[condition_div, right_side_of_cell])
                row.children.append(cell)
            left_side.children.append(row)
        else:
            # Row 6 — only one cell, left aligned
            single_row = LayoutDivision(flow_direction=FlowDirection.RIGHT, children=[])
            cell = LayoutDivision(flow_direction=FlowDirection.RIGHT, children=[])
            condition_div = TextDivision(
                text_callback=dummy_text(f"Condition {row_index}-0"),
                text_style=TEXT_STYLES["condition"]
            )
            cell.children.append(condition_div)
            single_row.children.append(cell)
            left_side.children.append(single_row)

    # Second child (RIGHT side) — 6 children
    right_side = LayoutDivision(flow_direction=FlowDirection.DOWN, children=[])

    for i in range(6):
        container = LayoutDivision()
        if i < 5:
            container.children.append(
                TextDivision(
                    text_callback=dummy_text(f"Row Mode Text {i}"),
                    text_style=TEXT_STYLES["row-mode"]
                )
            )
        right_side.children.append(container)

    # Add both sides to root
    root_layout.children.extend([left_side, right_side])
    return root_layout


def create_layout_2():
    player = Player([start.clone()], Agent("Player 1", 4), starting_tokens=0)
    player2 = Player([start.clone()], Agent("Player 2", 1), starting_tokens=1)
    random.seed(6)
    game = Game([player, player2])

    def get_tile(x: int, y: int):
        return game.tiles[7-y][x]

    def get_count(x: int, y: int):
        return game.get_tiles_available(get_tile(x, y))

    def get_side(y: int):
        return game.get_row_mode(7-y)

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

    layout = LayoutDivision(
        # padding=Spacing.axis(horiz=10),
        background_color=COLOR_DICT["background"],
        children=[

            LayoutDivision(
                # margin=Spacing.axis(vert=5),
                # padding=Spacing.all(5),
                # background_color=(255, 0, 0),
                children=[
                    LayoutDivision(
                        margin=Spacing.all(10),
                        padding=Spacing.all(5),
                        background_color=COLOR_DICT["tile_bg"],
                        horiz_alignment=0.5,
                        children=[
                            TextDivision(
                                text_callback=lambda x=game.get_condition(7-y, x).name: x,
                                text_style=FONT_DICT["condition"],
                                flex=1,
                                flex_weight=1,
                                vert_alignment=0.5,
                                horiz_alignment=0.5

                            ),
                            LayoutDivision(
                                background_color=COLOR_DICT[get_tile(x, y).type],
                                padding=Spacing.all(5),
                                flex_weight=5,
                                children=[
                                    LayoutDivision(
                                        children=[
                                            TextDivision(
                                                text_callback=lambda x=x, y=y: get_tile(x, y).name,
                                                text_style=FONT_DICT["title" if get_tile(
                                                    x, y).type is not TileType.YELLOW else "title-dark"],
                                                flex=1,
                                                horiz_alignment=0
                                            ),
                                            TextDivision(
                                                text_callback=lambda x=x, y=y: f"x{get_count(x, y)}",
                                                text_style=FONT_DICT["title" if get_tile(
                                                    x, y).type is not TileType.YELLOW else "title-dark"],
                                                flex=1,
                                                horiz_alignment=1
                                            ),
                                        ],
                                        flow_direction=FlowDirection.RIGHT
                                    ),
                                    TextDivision(
                                        text_callback=lambda x=x, y=y: get_tile(x, y).description,
                                        text_style=FONT_DICT["description" if get_tile(
                                            x, y).type is not TileType.YELLOW else "description-dark"],
                                        margin=Spacing.all(5),
                                        flex=1,
                                        flex_weight=4
                                    )
                                ]
                            )
                        ]
                    )
                    for x in range(4)
                ] + [
                    TextDivision(
                        text_callback=lambda y=y: f'{get_side(y).name} side',
                        text_style=FONT_DICT["side"],
                        margin=Spacing.all(10),
                        padding=Spacing.all(5)
                    )
                ],
                flow_direction=FlowDirection.RIGHT
            )
            for y in range(5)

        ]
    )

    return layout


def main():
    SCREEN_WIDTH = 1500
    SCREEN_HEIGHT = 1000
    running = True
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)

    # layout = LayoutDivision(background_color=(255, 0, 0), children=[TextDivision(
    #     lambda: "Use after claiming a tile (including possibly this one). Divide your locked dice into two groups. With each group, claim one yellow or blue tile that you don't already have.", TextStyle((0, 0, 0), "consolas", 14), flex=1)])

    layout = create_layout_2()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen_w, screen_h = screen.get_size()
        layout_surface = layout.draw((screen_w, (screen_h*2)//3))
        screen.blit(layout_surface, (0, 0))
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()


if __name__ == "__main__":
    main()
