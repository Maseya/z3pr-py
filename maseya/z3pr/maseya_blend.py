"""Define the maseya_blend function."""


from math import sqrt

from .color_f import ColorF


def maseya_blend(
    color: ColorF, changes: ColorF
) -> ColorF:  # pylint: disable=invalid-name
    """Change a color value but keep it visually pleasing."""
    # Ensure at least a 2.5% change in hue.
    hue = (changes.red * 0.95) + 0.025 + color.hue

    chroma_shift = changes.green - 0.5
    x_chroma = color.chroma
    chroma = x_chroma
    if chroma_shift > 0:
        # Put heavy limitations on oversaturating colors.
        chroma *= 1 + ((1 - x_chroma) * chroma_shift * 0.5)

    else:
        # Put no limitation on desaturating colors. However, make it more
        # likely that only a little desaturation will occur.
        chroma *= sqrt(1 - pow(chroma_shift * 2, 2))

    luma_shift = changes.blue - 0.5
    x_luma = color.luma
    luma = x_luma
    if luma_shift > 0:
        # Do not heavily brighten colors. However, if we removed a lot of
        # saturation, then we can allow for some brighter colors.
        chroma_diff = max(x_chroma - chroma, 0)
        luma *= 1 + ((1 - x_luma) * luma_shift * (1 + chroma_diff))

    else:
        # Do not colors get too dark.
        luma *= 1 + (luma_shift / 2)

    return ColorF.from_hcy(hue, chroma, luma)
