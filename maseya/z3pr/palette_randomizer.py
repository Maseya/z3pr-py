import json
import os
from random import Random

from typing import List

from .color_f import ColorF
from .palette_editor import PaletteEditor
from .maseya_blend import maseya_blend


def _read_internal_json(json_path):
    """Read JSON file in internal "data" folder."""
    # The data folder should be relative to this source file.
    fdir = os.path.dirname(os.path.abspath(__file__))

    # The JSON file is located in a "data" folder.
    json_fpath = os.path.join(fdir, "data", json_path)
    with open(json_fpath) as stream:
        return json.load(stream)


def build_offsets_array(options: dict):
    """Build offset array from several offset arrays."""

    def try_get_offset_array(name: str) -> List[int]:
        if options.get(f"randomize_{name}", False):
            return _read_internal_json(f"{name}.json")
        return []

    offsets = []
    for name in ["dungeon", "hud", "link_sprite", "sword", "shield", "overworld"]:
        offsets.extend(try_get_offset_array(name))
    return offsets


def _random_color(seed: int = -1):
    """Generate random colors with an optional seed value."""
    random = Random(seed) if seed != -1 else Random()

    def next_color():
        return ColorF(random.random(), random.random(), random.random())

    return next_color


def randomize(rom: bytearray, mode: str, next_color_func, options=dict):
    """Randomize palette data in a rom."""
    # We want to do case-invariant searches
    mode = mode.lower()

    # Skip all calculations if "none" is passed.
    if mode == "none":
        return

    # Get the basic algorithms and offer some variant spellings just in case.
    algorithm_tuples = {
        "maseya": [maseya_blend, next_color_func],
        "grayscale": [lambda x, y: x.grayscale, lambda: None],
        "negative": [lambda x, y: x.inverse, lambda: None],
        "blackout": [lambda x, y: y, lambda: ColorF(0, 0, 0)],
    }
    algorithm_tuples["default"] = algorithm_tuples["maseya"]
    algorithm_tuples["greyscale"] = algorithm_tuples["grayscale"]
    algorithm_tuples["invert"] = algorithm_tuples["negative"]
    algorithm_tuples["inverse"] = algorithm_tuples["negative"]
    algorithm_tuples["inverted"] = algorithm_tuples["negative"]

    # Now see which algorithm tuple we actually want.
    blend_func, blend_color_func = algorithm_tuples[mode]

    # Get array of offset collections. Each offset collection specifies a grouping
    # palette data that should be blended by the same rules.
    offsets_array = build_offsets_array(options)

    # Create a palette editor for each offset collection.
    palette_editors = [PaletteEditor(rom, offsets) for offsets in offsets_array]

    # Blend colors in each palette editor then write it back to rom.
    for palette_editor in palette_editors:
        palette_editor.blend(blend_func, blend_color_func)
        palette_editor.write_to_rom(rom)


def append_to_file_name(base_name: str, text_to_append: str) -> str:
    """Append text to file name and preserve extension."""
    fname, ext = os.path.splitext(base_name)
    return fname + text_to_append + ext


def randomize_from_options(options):
    """Randomize palette data in a file and output it to a new file."""
    options = dict(options)
    input_path = options.pop("input_file")
    output_path = options.pop("output_file", "")
    output_json = options.pop("use_json", False)

    if not output_path:
        if output_json:
            output_path = os.path.splitext(input_path)[0] + ".json"
        else:
            output_path = append_to_file_name(input_path, "-rand-pal")
    else:
        output_path = options.output_path

    next_color = _random_color(options.pop("seed", -1))
    with open(input_path, mode="rb") as stream:
        rom = bytearray(stream.read())

    randomize(rom, options.pop("mode", "default"), next_color, options)

    with open(output_path, mode="wb") as stream:
        stream.write(rom)
