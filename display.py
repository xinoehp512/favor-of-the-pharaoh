# Display
ESC = "\033"
RESET = f"{ESC}[0m"
BOLD = f"{ESC}[1m"


def FOREGROUND(x: int):
    return f"{ESC}[38;5;{x}m"


def BACKGROUND(x: int):
    return f"{ESC}[48;5;{x}m"


def COLOR(color: int, x: str):
    '''
    White 255\n
    Red 196\n
    Blue 21\n
    Green 76\n
    Black 234\n
    Gold 220\n
    Gray 110\n
    '''
    return f"{FOREGROUND(color)}{x}{RESET}"


def FB_COLOR(fore: int, back: int, x: str):
    return f"{FOREGROUND(fore)}{BACKGROUND(back)}{x}{RESET}"


SQUARE = "██"
HALF_SQUARE = "█"
BLACK_SQUARE = f"{FOREGROUND(0)}{SQUARE}{RESET}"
RED_SQUARE = f"{FOREGROUND(196)}{SQUARE}{RESET}"
BLUE_SQUARE = f"{FOREGROUND(21)}{SQUARE}{RESET}"
GREEN_SQUARE = f"{FOREGROUND(76)}{SQUARE}{RESET}"


class Screen:
    def __init__(self, values: list[list[str]]) -> None:
        self.values = [list(row) for row in values]

    @property
    def width(self):
        return len(self.values[0])

    @property
    def height(self):
        return len(self.values)

    def print(self):
        for row in self.values:
            for char in row:
                print(char, end="")
            print()

    def set_char(self, x: int, y: int, value: str):
        if x >= 0 and y >= 0 and y < len(self.values) and x < len(self.values[y]):
            self.values[y][x] = value


class Text_Canvas:
    def __init__(self, width: int, height: int) -> None:
        self.screen = Screen([[HALF_SQUARE]*width]*height)
        self.width = width
        self.height = height

    def draw_text(self, x: int, y: int, text: str, fcolor: int, bcolor: int):
        for i, char in enumerate(text):
            self.screen.set_char(x+i, y, FB_COLOR(fcolor, bcolor, char))

    def draw_rect(self, x: int, y: int, w: int, h: int, color: int):
        for i in range(w):
            for j in range(h):
                self.screen.set_char(x+i, y+j, COLOR(color, HALF_SQUARE))

    def display(self):
        self.screen.print()

    def clear(self):
        self.screen = Screen([[HALF_SQUARE]*self.width]*self.height)
