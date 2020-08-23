"""Tests for blending algorithms on rom data."""

import json
import os
from typing import Iterable, List, Mapping, Tuple

from maseya.z3pr.color_f import ColorF
from maseya.z3pr.palette_randomizer import randomize
from maseya.z3pr.math_helper import powerset

# Minimum LTTP rom size is 2MB.
TEST_ROM_SIZE = 0x200000

# These represent the palette subsets we can individually modify.
SUBSETS = ["dungeon", "sword", "shield", "overworld"]


def _read_internal_json(
    json_path: str,
) -> Mapping[str, Mapping[str, Mapping[str, List[int]]]]:
    """Read a JSON file in relative "data" directory."""
    fdir = os.path.dirname(os.path.abspath(__file__))
    json_fpath = os.path.join(fdir, "data", f"{json_path}.json")
    with open(json_fpath) as stream:
        return json.load(stream)


def _iterate_offsets(
    data: Mapping[str, Mapping[str, Mapping[str, List[int]]]], args: Iterable[str]
) -> Iterable[Tuple[int, int]]:
    """Get all offsets from given args in a JSON file."""
    # We only want the data of the given args.
    for arg in args:
        # Get the "raw" and "oam" offset arrays.
        for arrays in [data[arg].get(key, dict()) for key in ["raw", "oam"]]:
            # Get the offset collection.
            for index, array in arrays.items():
                # Yield each offset in rom that the value belongs to.
                offset = int(index)
                for i, value in enumerate(array):
                    yield offset + i, value


def _initialize_test_rom(
    data: Mapping[str, Mapping[str, Mapping[str, List[int]]]], args: Iterable[str]
):
    """Construct test rom using JSON fill data."""
    rom = bytearray(TEST_ROM_SIZE)
    # Write data specific in JSON file.
    for offset, value in _iterate_offsets(data, args):
        rom[offset] = value
    return rom


def _assert_changes_to_rom(
    rom: bytearray,
    data: Mapping[str, Mapping[str, Mapping[str, List[int]]]],
    args: Iterable[str],
):
    """Determine that rom data's changes match our expected data."""
    for offset, value in _iterate_offsets(data, args):
        assert (
            value == rom[offset]
        ), f"Failed at offset={offset}. Expected={value}; Actual={rom[offset]}"


def _assert_blackout_to_rom(
    rom: bytearray,
    data: Mapping[str, Mapping[str, Mapping[str, List[int]]]],
    args: Iterable[str],
):
    """Determine that rom palette data is all black colors."""
    # We only test the args we're actuall modifying.
    for arg in args:
        # We test the raw palette data first, which should have all zeros.
        raw = data[arg].get("raw", [])
        for index in raw:
            offset = int(index)
            for i in range(len(raw[index])):
                assert rom[offset + i] == 0

        # OAM Palette data is a bit more tricky, that's just how SNES code works...
        # Red, Green, and Blue channels are ORed with 0x20, 0x40, and 0x80 respectively.
        oam = data[arg].get("oam", [])
        for index in oam:
            offset = int(index)
            # Test that red channel is zero.
            assert rom[offset + 0] == 0x20

            # Green channel shows up twice. Make sure both are zero.
            assert rom[offset + 1] == 0x40
            assert rom[offset + 3] == 0x40

            # Finally, blue channel must be zero.
            assert rom[offset + 4] == 0x80


def _generate_options(args: Iterable[str]) -> Mapping[str, bool]:
    """Generate command-line flags from given test args."""
    return {f"randomize_{arg}": True for arg in args}


def test_no_randomize():
    """Assert that passing "None" will not change the rom data."""
    # Get base palette data.
    data = _read_internal_json("base")

    # Run test for all palette subsets.
    for args in powerset(SUBSETS):
        options = _generate_options(args)
        rom = _initialize_test_rom(data, args)
        randomize(rom, "None", None, options)
        _assert_changes_to_rom(rom, data, args)


def test_blackout():
    """Assert that passing "Blackout" will make an all-black palette."""
    # Get base palette data.
    data = _read_internal_json("base")

    # Run test for all palette subsets.
    for args in powerset(SUBSETS):
        options = _generate_options(args)
        rom = _initialize_test_rom(data, args)
        randomize(rom, "Blackout", None, options)
        _assert_blackout_to_rom(rom, data, args)


def test_invert():
    """Assert that passing "Negative" will invert the color palette."""
    # Get base palette data.
    data = _read_internal_json("base")

    # Run test for all palette subsets.
    expected = _read_internal_json("negative")
    for args in powerset(SUBSETS):
        options = _generate_options(args)
        rom = _initialize_test_rom(data, args)
        randomize(rom, "Negative", None, options)
        _assert_changes_to_rom(rom, expected, args)


def test_grayscale():
    """Assert that passing "Grayscale" will gray out the palette."""
    # Get base palette data.
    data = _read_internal_json("base")

    # Run test for all palette subsets.
    expected = _read_internal_json("grayscale")
    for args in powerset(SUBSETS):
        options = _generate_options(args)
        rom = _initialize_test_rom(data, args)
        randomize(rom, "Grayscale", None, options)
        _assert_changes_to_rom(rom, expected, args)


def _get_stored_random_colors(
    data: Mapping[str, Mapping[str, Mapping[str, List[int]]]], args: Iterable[str]
):
    """Get deterministically generated color values from JSON data."""
    random_values = []

    # Get color values for all palette subsets we are using.
    for arg in args:
        # Get RGB colors from "random" key in JSON file.
        for array in data[arg]["random"]:
            random_values.append(ColorF(*array))
    return random_values


def test_maseya_blend():
    """Assert that passing "Default" will perform the desired Maseya blend."""
    # Get base palette data.
    data = _read_internal_json("base")

    # Get the color data we'll be expecting from the final rom product.
    expected = _read_internal_json("maseya")

    # Declare this array now so `next_color` can use it as nonlocal.
    random_values = []

    # Run test for all palette subsets.
    for args in powerset(SUBSETS):
        next_color_index = 0
        random_values = _get_stored_random_colors(expected, args)

        def next_color():
            """Generate colors from our JSON test data."""
            nonlocal next_color_index
            nonlocal random_values
            result = random_values[next_color_index]
            next_color_index += 1
            return result

        options = _generate_options(args)
        rom = _initialize_test_rom(data, args)
        randomize(rom, "Default", next_color, options)
        _assert_changes_to_rom(rom, expected, args)
