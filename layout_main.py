
import random
from enums import TileType
from game_io import ConsoleIO
from layout_division import *
from main import Game
from player import Player
from tile import *


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
    player = Player([start.clone()], ("Player 1", 4), ConsoleIO(), starting_tokens=0)
    player2 = Player([start.clone()], ("Player 2", 1), ConsoleIO(), starting_tokens=1)
    random.seed(6)
    game = Game([player, player2])

    def get_tile(x: int, y: int):
        return game.tiles[7-y][x]

    def get_count(x: int, y: int):
        return game.get_tile_amount(get_tile(x, y))

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
