"""Define primary palette randomizer functions."""

import json
import os
from random import Random

from typing import List, Mapping

from .color_f import ColorF
from .palette_editor import PaletteEditor
from .maseya_blend import maseya_blend, acid_blend


def _read_internal_json(json_path: str, json_dir: str = None):
    """Read JSON file in internal "data" folder."""
    # The data folder should be relative to this source file.
    if not json_dir:
        json_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

    # The JSON file is located in a "data" folder.
    json_fpath = os.path.join(json_dir, json_path)
    with open(json_fpath) as stream:
        return json.load(stream)


def build_offsets_array(
    options: Mapping[str, bool], json_dir: str = None
) -> List[List[int]]:
    """Build offset array from several offset arrays."""

    def try_get_offset_array(name: str) -> List[int]:
        if options.get(f"randomize_{name}", False):
            return _read_internal_json(f"{name}.json", json_dir)
        return []

    offsets = []
    # TODO(bonimy): Add the other palette data like sprites.
    for name in ["dungeon", "hud", "link_sprite", "sword", "shield", "overworld"]:
        offsets.extend(try_get_offset_array(name))
    return offsets


def _random_color_generator(seed: int = -1):
    """Generate random colors with an optional seed value."""
    random = Random(seed) if seed != -1 else Random()

    def next_color():
        return ColorF(random.random(), random.random(), random.random())

    return next_color


def randomize(
    rom: bytearray,
    mode: str,
    next_color=None,
    options: dict = None,
    json_dir: str = None,
):
    """Randomize palette data in a rom."""
    # We want to do case-invariant searches
    mode = mode.lower()

    # Skip all calculations if "none" is passed.
    if mode == "none":
        return

    # Create standard random generator if no generator was given.
    if not next_color:
        next_color = _random_color_generator()

    # Get array of offset collections. Each offset collection specifies a grouping
    # palette data that should be blended by the same rules.
    offsets_array = build_offsets_array(options, json_dir)

    # Create a palette editor for each offset collection.
    palette_editors = [PaletteEditor(rom, offsets) for offsets in offsets_array]

    # Get the basic algorithms and offer some variant spellings just in case.
    algorithm_tuples = {
        "maseya": [maseya_blend, next_color, PaletteEditor.blend],
        "grayscale": [lambda x, y: x.grayscale, lambda: None, PaletteEditor.blend],
        "negative": [lambda x, y: x.inverse, lambda: None, PaletteEditor.blend],
        "blackout": [lambda x, y: y, lambda: ColorF(0, 0, 0), PaletteEditor.blend],
        "classic": [acid_blend, next_color, PaletteEditor.blend],
        "dizzy": [ColorF.hue_blend, next_color, PaletteEditor.blend_by_color,],
        "sick": [
            lambda x, y: ColorF.luma_blend(y, x),
            next_color,
            PaletteEditor.blend_by_color,
        ],
        "puke": [lambda x, y: y, next_color, PaletteEditor.blend_by_color],
    }
    algorithm_tuples["default"] = algorithm_tuples["maseya"]
    algorithm_tuples["greyscale"] = algorithm_tuples["grayscale"]
    algorithm_tuples["invert"] = algorithm_tuples["negative"]
    algorithm_tuples["inverse"] = algorithm_tuples["negative"]
    algorithm_tuples["inverted"] = algorithm_tuples["negative"]

    # Now see which algorithm tuple we actually want.
    color_blend, get_next_color, palette_blend = algorithm_tuples[mode]

    # Blend colors in each palette editor then write it back to rom.
    for palette_editor in palette_editors:
        palette_blend(palette_editor, color_blend, get_next_color)
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
    json_dir = options.pop("json_dir", "")

    # Infer output path from input path if no output was specified.
    if not output_path:
        output_path = append_to_file_name(input_path, "-rand-pal")

    # Define color-generating function.
    next_color = _random_color_generator(options.pop("seed", -1))

    # Read ROM data from file.
    with open(input_path, mode="rb") as stream:
        rom = bytearray(stream.read())

    # Randomize ROM data.
    randomize(rom, options.pop("mode", "default"), next_color, options, json_dir)

    # Write results to output file.
    with open(output_path, mode="wb") as stream:
        stream.write(rom)
