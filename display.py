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
