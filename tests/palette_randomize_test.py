"""Tests for blending algorithms on rom data."""

import json
import os
from typing import Iterable, List, Mapping, Tuple

from maseya.z3pr.color_f import ColorF
from maseya.z3pr.palette_randomizer import (
    randomize,
    build_offset_collections,
    cache_offset_collections,
    iterate_cached_offset_collections,
)
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
        for offset_dicts in [data[arg].get(key, dict()) for key in ["raw", "oam"]]:
            # Get the offset collection.
            for index, offset_collection in offset_dicts.items():
                # Yield each offset in rom that the value belongs to.
                offset = int(index)
                for i, value in enumerate(offset_collection):
                    yield offset + i, value


def _initialize_test_rom(data: Iterable[Tuple[int, int]]):
    """test rom using JSON fill data."""
    rom = bytearray(TEST_ROM_SIZE)
    # Write data specific in JSON file.
    for offset, value in data:
        rom[offset] = value
    return rom


def _assert_values_in_rom(rom: bytearray, data: Iterable[Tuple[int, int]]):
    """Determine that rom data's changes match our expected data."""
    for offset, value in data:
        assert (
            value == rom[offset]
        ), f"Failed at offset={offset}. Expected={value}; Actual={rom[offset]}"


def _assert_blackout_to_rom(
    rom: bytearray,
    data: Mapping[str, Mapping[str, Mapping[str, List[int]]]],
    args: Iterable[str],
):
    """Determine that rom palette data is all black colors."""
    # We only test the args we're actually modifying.
    for arg in args:
        # We test the raw palette data first, which should have all zeros.
        raw = data[arg].get("raw", [])
        for index in raw:
            offset = int(index)
            assert rom[offset + 0] == 0
            assert rom[offset + 1] == 0

        # OAM Palette data is a bit more tricky red, green, and blue channels are
        # bitwise "OR"ed with 0x20, 0x40, and 0x80 respectively.
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


def _get_stored_random_colors(
    data: Mapping[str, Mapping[str, Mapping[str, List[int]]]], args: Iterable[str]
) -> List[ColorF]:
    """Get deterministically generated color values from JSON data."""
    result = []

    # Get color values for all palette subsets we are using.
    for arg in args:
        # Get RGB colors from "random" key in JSON file.
        for array in data[arg].get("random", list()):
            result.append(ColorF(*array))
    return iter(result) if len(result) > 0 else None


def _assert_blend(name: str):
    """Assert that passing a blend option does the intended blend."""
    # Get base palette data.
    data = _read_internal_json("base")

    # Get the color data we'll be expecting from the final rom product.
    expected = _read_internal_json(name)

    # Run test for all palette subsets.
    for args in powerset(SUBSETS):
        # Get deterministic color generator for testing.
        random_values = _get_stored_random_colors(expected, args)

        options = _generate_options(args)
        rom = _initialize_test_rom(_iterate_offsets(data, args))
        offset_collections = build_offset_collections(options)
        randomize(rom, name, offset_collections, random_values)
        _assert_values_in_rom(rom, _iterate_offsets(expected, args))


def test_no_randomize():
    """Assert that passing "None" will not change the rom data."""
    # Get base palette data.
    data = _read_internal_json("base")

    # Run test for all palette subsets.
    for args in powerset(SUBSETS):
        options = _generate_options(args)
        rom = _initialize_test_rom(_iterate_offsets(data, args))
        offset_collections = build_offset_collections(options)
        randomize(rom, "None", offset_collections)
        _assert_values_in_rom(rom, _iterate_offsets(data, args))


def test_blackout():
    """Assert that passing "Blackout" will make an all-black palette."""
    # Get base palette data.
    data = _read_internal_json("base")

    # Run test for all palette subsets.
    for args in powerset(SUBSETS):
        options = _generate_options(args)
        rom = _initialize_test_rom(_iterate_offsets(data, args))
        offset_collections = build_offset_collections(options)
        randomize(rom, "Blackout", offset_collections)
        _assert_blackout_to_rom(rom, data, args)


def test_invert():
    _assert_blend("negative")


def test_grayscale():
    _assert_blend("grayscale")


def test_maseya_blend():
    """Assert that passing "Default" will perform the desired Maseya blend."""
    _assert_blend("maseya")


def test_classic_blend():
    """Assert that passing "Clasic" will perform the desired dizzy blend."""
    _assert_blend("classic")


def test_dizzy_blend():
    """Assert that passing "Dizzy" will perform the desired classic blend."""
    _assert_blend("dizzy")


def test_sick_blend():
    """Assert "Sick" blend."""
    _assert_blend("sick")


def test_puke_blend():
    """Assert "Puke" blend."""
    _assert_blend("puke")


def test_cached_randomize_with_blackout():
    """Assert blackout mode with cached offset array."""
    # Cache JSON data into memory.
    offsets_array_cache = cache_offset_collections()

    # Get base palette data.
    data = _read_internal_json("base")

    # Run test for all palette subsets.
    for args in powerset(SUBSETS):
        options = _generate_options(args)
        rom = _initialize_test_rom(_iterate_offsets(data, args))
        offset_collections = iterate_cached_offset_collections(
            offsets_array_cache, options
        )
        randomize(rom, "Blackout", offset_collections)
        _assert_blackout_to_rom(rom, data, args)


def test_cached_randomize_with_maseya_blend():
    """Assert maseya blend mode with cached offset array."""
    # Cache JSON data into memory.
    cached_offset_collections = cache_offset_collections()

    # Get base palette data.
    data = _read_internal_json("base")

    # Get the color data we'll be expecting from the final rom product.
    expected = _read_internal_json("maseya")

    # Run test for all palette subsets.
    for args in powerset(SUBSETS):
        # Get deterministic color generator for testing.
        random_values = _get_stored_random_colors(expected, args)

        options = _generate_options(args)
        rom = _initialize_test_rom(_iterate_offsets(data, args))
        offset_collections = iterate_cached_offset_collections(
            cached_offset_collections, options
        )
        randomize(rom, "Maseya", offset_collections, random_values)
        _assert_values_in_rom(rom, _iterate_offsets(expected, args))
