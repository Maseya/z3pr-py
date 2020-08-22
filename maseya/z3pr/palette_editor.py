from typing import Callable, List

from .snes_color import SnesColor
from .color_f import ColorF


class PaletteEditor:
    def __init__(self, rom: bytearray, offsets: List[int]):
        def raw(offset: int) -> SnesColor:
            return SnesColor.from_high_and_low(rom[offset], rom[offset + 1])

        def oam(offset: int) -> SnesColor:
            return SnesColor.from_rgb(
                rom[offset] & 0x1F, rom[offset + 1] & 0x1F, rom[offset + 4] & 0x1F
            )

        def get_color(offset: int) -> SnesColor:
            return raw(offset) if offset >= 0 else oam(-offset)

        self.__items = {offset: get_color(offset).to_color_f() for offset in offsets}

    def blend(
        self,
        blend_func: Callable[[ColorF, ColorF], ColorF],
        blend_color_func: Callable[[], ColorF],
    ):
        blend_color = blend_color_func()
        for offset in self.__items.keys():
            self.__items[offset] = blend_func(self.__items[offset], blend_color)

    def write_to_rom(self, rom: bytearray):
        def raw(offset: int, color: SnesColor):
            rom[offset + 0] = color.low
            rom[offset + 1] = color.high

        def oam(offset: int, color: SnesColor):
            rom[offset + 0] = color.red | 0x20
            rom[offset + 1] = color.green | 0x40
            rom[offset + 3] = color.green | 0x40
            rom[offset + 4] = color.blue | 0x80

        def write_color(offset: int, color: SnesColor):
            if offset >= 0:
                raw(offset, color)
            else:
                oam(-offset, color)

        for offset, color in self.__items.items():
            write_color(offset, SnesColor.from_color_f(color))
