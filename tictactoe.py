import pygame

from layout_division import BorderStyle, FlowDirection, LayoutDivision, TextDivision, TextStyle


def create_layout():
    COLOR_DICT: dict[str, tuple[int, int, int]] = {
        "background": (30, 30, 30),
        "tile_bg": (60, 60, 60),
        "text": (255, 255, 255),
        "text-dark": (30, 30, 30),
        "gray": (180, 180, 180),
    }
    text_style = TextStyle((255, 255, 255), "consolas", 100)
    layout = LayoutDivision(
        background_color=COLOR_DICT["background"],
        children=[
            LayoutDivision(
                flow_direction=FlowDirection.RIGHT,
                children=[
                    LayoutDivision(
                        border=BorderStyle(2, COLOR_DICT["gray"]),
                        background_color=COLOR_DICT['tile_bg'],
                        vert_alignment=0.5,
                        horiz_alignment=0.5,
                        children=[
                            TextDivision(
                                text_callback=lambda: "X",
                                text_style=text_style,
                            )
                        ]
                    )
                    for _x in range(3)
                ]
            )
            for _y in range(3)
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

    layout = create_layout()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        layout_surface = layout.draw(screen.get_size())
        screen.blit(layout_surface, (0, 0))
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()


if __name__ == "__main__":
    main()
