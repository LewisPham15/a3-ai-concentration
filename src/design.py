"""Shared visual tokens, so four separately written panels read as one app.

Colour is the one encoding that crosses panel boundaries: a reader who learns
in panel 2 that a hue means China carries that into panel 3. The palette is
Okabe-Ito, eight hues that stay separable under the common forms of colour
vision deficiency and that also separate by lightness in greyscale.
"""

PALETTE = [
    "#0072b2",  # blue
    "#e69f00",  # orange
    "#009e73",  # green
    "#cc79a7",  # pink
    "#d55e00",  # vermillion
    "#56b4e9",  # sky
    "#f0e442",  # yellow
    "#000000",  # black
]

INK = "#1c1c18"
FAINT = "#8c8c84"
GHOST = "#d9d9d2"
REST = "#b9b9b0"          # anything pooled into "other"

SECTOR_COLOURS = {
    "Industry": PALETTE[0],
    "Academia": PALETTE[1],
    "Industry - Academia Collaboration": PALETTE[2],
    "Research collective": PALETTE[3],
    "Government": PALETTE[4],
    "Not stated": REST,
}

# Reported figures are drawn solid, estimated or derived ones dashed, in every
# panel. Panel 4 depends on this: its subject is which numbers are observed
# and which are inferred.
SOLID = None
DASH = "dash"


def hue(index):
    """A stable colour for the nth category within a panel."""
    return PALETTE[index % len(PALETTE)]
