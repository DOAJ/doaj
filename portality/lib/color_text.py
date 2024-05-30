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
