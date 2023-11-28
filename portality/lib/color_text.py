"""
Those are ANSI terminal escape codes. Specifically, they're "select graphic rendition" (SGR) escape codes, which consist of:

the "command sequence introducer", consisting of the characters \x1B (ESC) and [,
one or more numeric commands, separated by semicolons, and
the letter m, ending the code and indicating that this is an SGR code.
There are many possible numeric commands (and many other escape codes besides SGR), but the most relevant ones are:

30–37: set text color to one of the colors 0 to 7,
40–47: set background color to one of the colors 0 to 7,
39: reset text color to default,
49: reset background color to default,
1: make text bold / bright (this is the standard way to access the bright color variants),
22: turn off bold / bright effect, and
0: reset all text properties (color, background, brightness, etc.) to their default values.
Thus, for example, one could select bright purple text on a green background (eww!) with the code \x1B[35;1;42m.


------------------------

0	reset all SGR effects to their default
1	bold or increased intensity
2	faint or decreased intensity
4	singly underlined
5	slow blink
30-37	foreground color (8 colors)
38;5;x	foreground color (256 colors, non-standard)
38;2;r;g;b	foreground color (RGB, non-standard)
40-47	background color (8 colors)
48;5;x	background color (256 colors, non-standard)
48;2;r;g;b	background color (RGB, non-standard)
90-97	bright foreground color (non-standard)
100-107	bright background color (non-standard)

0	black
1	red
2	green
3	yellow
4	blue
5	magenta
6	cyan
7	white

ref:
* https://stackoverflow.com/questions/23975735/what-is-this-u001b9-syntax-of-choosing-what-color-text-appears-on-console#23977880
* https://chrisyeh96.github.io/2020/03/28/terminal-colors.html

"""
from enum import Enum
from typing import Union

reset_code = "\u001b[0m"


class Color(Enum):
    black = 0
    red = 1
    green = 2
    yellow = 3
    blue = 4
    magenta = 5
    cyan = 6
    white = 7


ColorLike = Union[Color, int]


def apply_color(text,
                front: ColorLike = None,
                background: ColorLike = None,
                bold=False, faint=False, underline=False,
                blink=False) -> str:
    def _to_color_idx(_input: ColorLike):
        if isinstance(_input, Color):
            return _input.value
        return _input

    color_code_list = []
    if front is not None:
        color_code_list.append(30 + _to_color_idx(front))

    if background is not None:
        color_code_list.append(40 + _to_color_idx(background))

    if bold:
        color_code_list.append(1)

    if faint:
        color_code_list.append(2)

    if underline:
        color_code_list.append(4)

    if blink:
        color_code_list.append(5)

    if not color_code_list:
        return f'{text}'

    color_start_code = ';'.join(map(str, color_code_list))
    color_start_code = f'\u001b[{color_start_code}m'
    return f'{color_start_code}{text}{reset_code}'
