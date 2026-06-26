# -*- coding: utf-8 -*-
"""Astro-Nex symbol font registration and glyph maps for the cairo renderer.

The bundled ``Astro-Nex.ttf`` maps ordinary Latin characters to astrological
symbols (zodiac signs + planets). The legacy GTK app simply called
``cr.select_font_face('Astro-Nex')`` after registering the font with
fontconfig. On this macOS / cairo 1.29 build that path does NOT work: cairo's
toy font API silently falls back to the system sans font and renders the
literal Latin letter (verified -- ``select_font_face('Astro-Nex')`` produces
pixel-identical output to ``select_font_face('sans-serif')``).

WORKING PATH (what this module uses): load the TTF directly through FreeType
and wrap it as a real ``cairo_font_face_t`` via ``cairo_ft_font_face_create_
for_ft_face``, then push it onto the context with ``cairo_set_font_face`` on
the raw ``cairo_t*`` pulled out of the pycairo Context object. This bypasses
fontconfig name resolution entirely and renders the true symbol glyphs.

If FreeType / cairo-ft cannot be bound (e.g. libraries missing), font loading
fails gracefully: ``set_symbol_font`` returns False and callers fall back to
short text labels in the default sans font so the wheel is still populated.

Public API:
    ZODIAC_GLYPHS  -- 12 chars, index 0..11 (aries..piscis)
    PLANET_GLYPHS  -- 11 chars, index 0..10 (sun,moon,..,pluto,node)
    FONT_FACE      -- the toy-font family name ('Astro-Nex'); kept for parity
    register_font()      -- fontconfig app-font registration (legacy parity)
    set_symbol_font(cr)  -- push the real symbol font onto a context; True/False
    font_available()     -- whether the symbol glyphs can actually be rendered
"""

import ctypes
import ctypes.util
from pathlib import Path

# index 0..11: aries, taurus, gemini, cancer, leo, virgo,
#              libra, scorpio, sagittarius, capricorn, aquarius, piscis
ZODIAC_GLYPHS = "qwertyuiopas"
# index 0..10: sun, moon, mercury, venus, mars, jupiter,
#              saturn, uranus, neptune, pluto, node
PLANET_GLYPHS = "dfhjklgzxcv"
FONT_FACE = "Astro-Nex"

_FONT = str(Path(__file__).parent.parent / "data" / "Astro-Nex.ttf")


def register_font():
    """Register the bundled TTF as a fontconfig app font (legacy parity).

    Kept because the legacy stack relied on it; on this build it succeeds but
    is not sufficient for cairo's toy API to actually use the font (see module
    docstring). Returns True if fontconfig accepted the file.
    """
    name = ctypes.util.find_library("fontconfig")
    if not name:
        return False
    try:
        fc = ctypes.CDLL(name)
        fc.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        return bool(fc.FcConfigAppFontAddFile(None, _FONT.encode("utf-8")))
    except OSError:
        return False


# --- FreeType + cairo-ft direct font loading (the path that actually works) ---

_FT_FONT_FACE = None  # cached cairo_font_face_t* (as int) once loaded
_CAIRO_LIB = None
_FONT_LOAD_ATTEMPTED = False


class _PycairoContext(ctypes.Structure):
    """Memory layout of pycairo's Context object: PyObject header then the
    ``cairo_t *ctx`` pointer. Lets us reach the raw cairo_t to call the cairo
    C API directly (pycairo exposes no public from-pointer font-face wrapper)."""
    _fields_ = [
        ("PyObject_HEAD", ctypes.c_byte * object.__basicsize__),
        ("ctx", ctypes.c_void_p),
        ("base", ctypes.c_void_p),
    ]


def _load_ft_font_face():
    """Build a cairo_font_face_t* from the bundled TTF via FreeType.

    Returns the pointer (int) on success, or None on any failure. Cached.
    """
    global _FT_FONT_FACE, _CAIRO_LIB, _FONT_LOAD_ATTEMPTED
    if _FONT_LOAD_ATTEMPTED:
        return _FT_FONT_FACE
    _FONT_LOAD_ATTEMPTED = True

    cairo_name = ctypes.util.find_library("cairo")
    ft_name = ctypes.util.find_library("freetype")
    if not cairo_name or not ft_name:
        return None
    try:
        cairo_lib = ctypes.CDLL(cairo_name)
        ft_lib = ctypes.CDLL(ft_name)

        FT_Library = ctypes.c_void_p
        FT_Face = ctypes.c_void_p

        ft_lib.FT_Init_FreeType.argtypes = [ctypes.POINTER(FT_Library)]
        lib = FT_Library()
        if ft_lib.FT_Init_FreeType(ctypes.byref(lib)) != 0:
            return None

        ft_lib.FT_New_Face.argtypes = [
            FT_Library, ctypes.c_char_p, ctypes.c_long, ctypes.POINTER(FT_Face)
        ]
        face = FT_Face()
        if ft_lib.FT_New_Face(lib, _FONT.encode("utf-8"), 0, ctypes.byref(face)) != 0:
            return None

        cairo_lib.cairo_ft_font_face_create_for_ft_face.restype = ctypes.c_void_p
        cairo_lib.cairo_ft_font_face_create_for_ft_face.argtypes = [FT_Face, ctypes.c_int]
        ff = cairo_lib.cairo_ft_font_face_create_for_ft_face(face, 0)
        if not ff:
            return None

        cairo_lib.cairo_set_font_face.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        # Keep references alive for the process lifetime: the ft lib, the FT
        # library handle and face back the cairo font face.
        _load_ft_font_face._refs = (ft_lib, lib, face)
        _CAIRO_LIB = cairo_lib
        _FT_FONT_FACE = ff
        return ff
    except OSError:
        return None


def set_symbol_font(cr):
    """Push the Astro-Nex symbol font onto the pycairo Context ``cr``.

    Returns True if the real symbol font was applied (callers should use the
    glyph chars), False if it could not be loaded (callers should fall back to
    text labels in the default font).
    """
    ff = _load_ft_font_face()
    if ff is None:
        return False
    try:
        cairo_t = _PycairoContext.from_address(id(cr)).ctx
        _CAIRO_LIB.cairo_set_font_face(cairo_t, ff)
        return True
    except (OSError, ValueError):
        return False


def font_available():
    """True if the Astro-Nex symbol glyphs can actually be rendered."""
    return _load_ft_font_face() is not None


# Register with fontconfig at import time for legacy parity / harmless side
# effect; the real rendering relies on set_symbol_font().
register_font()
