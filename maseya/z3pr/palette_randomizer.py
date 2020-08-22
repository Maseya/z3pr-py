import json
import os
from random import Random

from typing import List

from .color_f import ColorF
from .palette_editor import PaletteEditor
from .maseya_blend import maseya_blend


def _read_internal_json(json_path):
    fdir = os.path.dirname(os.path.abspath(__file__))
    json_fpath = os.path.join(fdir, "data", json_path)
    with open(json_fpath) as stream:
        return json.load(stream)


def get_offsets(json_path: str):
    return _read_internal_json(json_path)


def build_offsets_array(options: dict):
    def try_get_offsets(name: str) -> List[int]:
        if options.get(f"randomize_{name}", False):
            return get_offsets(f"{name}.json")
        return []

    offsets = []
    for name in ["dungeon", "hud", "link_sprite", "sword", "shield", "overworld"]:
        offsets.extend(try_get_offsets(name))
    return offsets


def _random_color(seed: int):
    random = Random(seed) if seed != -1 else Random()

    def next_color():
        return ColorF(random.random(), random.random(), random.random())

    return next_color


def randomize(rom: bytearray, mode: str, next_color_func=None, options=dict):
    mode = mode.lower()
    if mode == "none":
        return
    if mode == "default":
        mode = "maseya"

    if not next_color_func:
        next_color_func = _random_color(options.get("seed", -1))

    algorithms = {
        "maseya": [maseya_blend, next_color_func],
        "grayscale": [lambda x, y: x.grayscale, lambda: None],
        "negative": [lambda x, y: x.inverse, lambda: None],
        "blackout": [lambda x, y: y, lambda: ColorF(0, 0, 0)],
    }

    algorithm = algorithms[mode]

    offsets_array = build_offsets_array(options)
    palette_editors = [PaletteEditor(rom, offsets) for offsets in offsets_array]
    for palette_editor in palette_editors:
        palette_editor.blend(algorithm[0], algorithm[1])
        palette_editor.write_to_rom(rom)
