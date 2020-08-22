import json
import os
from typing import Iterable, List, Mapping, Tuple

from maseya.z3pr.color_f import ColorF
from maseya.z3pr.palette_randomizer import randomize
from maseya.z3pr.math_helper import powerset

TEST_ROM_SIZE = 0x200000
SUBSETS = ["dungeon", "sword", "shield", "overworld"]


def _read_internal_json(
    json_path: str,
) -> Mapping[str, Mapping[str, Mapping[str, List[int]]]]:
    fdir = os.path.dirname(os.path.abspath(__file__))
    json_fpath = os.path.join(fdir, "data", f"{json_path}.json")
    with open(json_fpath) as stream:
        return json.load(stream)


def _iterate_offsets(
    data: Mapping[str, Mapping[str, Mapping[str, List[int]]]], args: Iterable[str]
) -> Iterable[Tuple[int, int]]:
    for arg in args:
        for arrays in [data[arg].get(key, dict()) for key in ["raw", "oam"]]:
            for index, array in arrays.items():
                offset = int(index)
                for i, value in enumerate(array):
                    yield offset + i, value


def _initialize_test_rom(
    data: Mapping[str, Mapping[str, Mapping[str, List[int]]]], args: Iterable[str]
):
    rom = bytearray(TEST_ROM_SIZE)
    for offset, value in _iterate_offsets(data, args):
        rom[offset] = value
    return rom


def _assert_changes_to_rom(
    rom: bytearray,
    data: Mapping[str, Mapping[str, Mapping[str, List[int]]]],
    args: Iterable[str],
):
    for offset, value in _iterate_offsets(data, args):
        assert (
            value == rom[offset]
        ), f"Failed at offset={offset}. Expected={value}; Actual={rom[offset]}"


def _assert_blackout_to_rom(
    rom: bytearray,
    data: Mapping[str, Mapping[str, Mapping[str, List[int]]]],
    args: Iterable[str],
):
    for arg in args:
        raw = data[arg].get("raw", [])
        for index in raw:
            offset = int(index)
            for i in range(len(raw[index])):
                assert rom[offset + i] == 0

        oam = data[arg].get("oam", [])
        for index in oam:
            offset = int(index)
            assert rom[offset + 0] == 0x20
            assert rom[offset + 1] == 0x40
            assert rom[offset + 3] == 0x40
            assert rom[offset + 4] == 0x80


def _generate_options(args: Iterable[str]) -> Mapping[str, bool]:
    return {f"randomize_{arg}": True for arg in args}


def test_no_randomize():
    data = _read_internal_json("base")
    for args in powerset(SUBSETS):
        options = _generate_options(args)
        rom = _initialize_test_rom(data, args)
        randomize(rom, "None", None, options)
        _assert_changes_to_rom(rom, data, args)


def test_blackout():
    data = _read_internal_json("base")
    for args in powerset(SUBSETS):
        options = _generate_options(args)
        rom = _initialize_test_rom(data, args)
        randomize(rom, "Blackout", None, options)
        _assert_blackout_to_rom(rom, data, args)


def test_invert():
    data = _read_internal_json("base")
    expected = _read_internal_json("negative")
    for args in powerset(SUBSETS):
        options = _generate_options(args)
        rom = _initialize_test_rom(data, args)
        randomize(rom, "Negative", None, options)
        _assert_changes_to_rom(rom, expected, args)


def test_grayscale():
    data = _read_internal_json("base")
    expected = _read_internal_json("grayscale")
    for args in powerset(SUBSETS):
        options = _generate_options(args)
        rom = _initialize_test_rom(data, args)
        randomize(rom, "Grayscale", None, options)
        _assert_changes_to_rom(rom, expected, args)


def _get_stored_random_values(
    data: Mapping[str, Mapping[str, Mapping[str, List[int]]]], args: Iterable[str]
):
    random_values = []
    for arg in args:
        for array in data[arg]["random"]:
            random_values.append(ColorF(*array))
    return random_values


def test_maseya_blend():
    data = _read_internal_json("base")

    expected = _read_internal_json("maseya")
    random_values = []

    for args in powerset(SUBSETS):
        next_color_index = 0
        random_values = _get_stored_random_values(expected, args)

        def next_color():
            nonlocal next_color_index
            nonlocal random_values
            result = random_values[next_color_index]
            next_color_index += 1
            return result

        options = _generate_options(args)
        rom = _initialize_test_rom(data, args)
        randomize(rom, "Default", next_color, options)
        _assert_changes_to_rom(rom, expected, args)
