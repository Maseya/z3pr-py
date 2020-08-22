from maseya.z3pr.snes_color import SnesColor


def _invert_through_color_f(color: SnesColor) -> SnesColor:
    return SnesColor.from_color_f(color.to_color_f().inverse)


def test_conversion_betwen_color_f():
    for i in range(0x8000):
        expected_snes_color = SnesColor(i)
        color_f = expected_snes_color.to_color_f()
        actual_snes_color = SnesColor.from_color_f(color_f)
        assert expected_snes_color == actual_snes_color
