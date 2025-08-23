from __future__ import annotations

from typing import Callable, Optional
from enum import Enum
import pygame

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
