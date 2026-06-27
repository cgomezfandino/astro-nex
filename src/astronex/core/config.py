# -*- coding: utf-8 -*-
"""Configuration — port of ``astronex/config.py`` (issue #13).

Holds the default configuration constants, the :class:`NexConf` options object,
and the colour-parsing helpers consumed by the zodiac/render layers.

Port notes
----------
* The original used ``gtk.gdk.color_parse`` and divided GDK channels by 65535.
  Here colours are parsed directly from ``rrggbb`` hex strings to ``(r, g, b)``
  tuples in ``0..1`` (``hex_to_rgb``), removing the GTK dependency from the core.
* The original used the ``configobj`` library; the file format is a plain INI,
  so stdlib ``configparser`` semantics apply. ``read_config``/``reload_config``
  are ported for the I/O path; the parts that touch ``boss``/``state``/``pysw``
  (ephemeris path, favourites, orbs wiring) are wired up in later milestones.
* ``cfgcols`` is the module-level ``{name: '#rrggbb'}`` map populated by
  ``read_config`` / :func:`init_cfgcols`; the ``parse_*_colors`` helpers read it.
"""
import configparser
import os


# Original division factor used to normalise GDK 16-bit channels to 0..1.
MAGICK_COL = 65535.0

# ---------------------------------------------------------------------------
# Default constants (must match the original Astro-Nex exactly)
# ---------------------------------------------------------------------------
default_colors = {'pers': 'ff5600', 'tool': '0000ff',
                  'trans': '0000ff', 'node': '0000ff',
                  'fire': 'dd0000', 'earth': '00bb00', 'air': 'ffb600',
                  'water': '0000ff', 'orange': 'ff8000',
                  'green': '00cc00', 'blue': '0000f7',
                  'red': 'ee0000', 'click1': '3300e6',
                  'click2': 'cc001a', 'inv': '7f7f99', 'low': '7f997f',
                  'transcol': '7f7f99', 'overlay': '803480', 'clicksoul': 'c227ff'}
COLORS = default_colors
PNG = {'hsize': 600, 'vsize': 600, 'labels': 'true',
       'pngviewer': 'display', 'resolution': 300}
PDF = {'pdfviewer': 'kpdf'}
LANG = {'lang': 'es'}
FONT = {'font': 'Sans 11', 'transtyle': 'huber'}  # 'classic'
LINES = {'base': 0.85}
ORBS = {'transits': [1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 1.0],
        'lum': [3.0, 5.0, 6.0, 8.0, 9.0],
        'normal': [2.0, 4.0, 5.0, 6.0, 7.0],
        'short': [1.5, 3.0, 4.0, 5.0, 6.0],
        'far': [1.0, 2.0, 3.0, 4.0, 5.0],
        'useless': [1.0, 2.0, 2.0, 3.0, 4.0],
        'pelum': [3.0, 5.0, 6.0, 8.0, 9.0],
        'penormal': [2.0, 4.0, 5.0, 6.0, 7.0],
        'peshort': [1.5, 3.0, 4.0, 5.0, 6.0],
        'pefar': [1.0, 2.0, 3.0, 4.0, 5.0],
        'peuseless': [1.0, 2.0, 2.0, 3.0, 4.0],
        'discard': []}
DEFAULT = {'usa': 'false', 'favourites': '', 'nfav': 3, 'aux_size': 800,
           'database': 'personal', 'ephepath': 'ephe',
           'country': 'SP', 'region': 53,
           'locality': 'Las Palmas de Gran Canaria'}


class NexConf(object):
    """Options object aggregating every default section as attributes."""
    sections = {'DEFAULT': DEFAULT, 'ORBS': ORBS,
                'COLORS': COLORS, 'LINES': LINES,
                'FONT': FONT, 'PNG': PNG, 'LANG': LANG, 'PDF': PDF}

    def __init__(self):
        for sec in self.sections.values():
            self.__dict__.update(sec)
        # Determine UI language from the system locale. The original used the
        # now-deprecated locale.getdefaultlocale(); we use the environment-based
        # lookup which is stable across Python versions.
        lang = None
        for envvar in ('LC_ALL', 'LC_MESSAGES', 'LANG'):
            val = os.environ.get(envvar)
            if val:
                lang = val.split('.')[0]
                break
        if lang:
            lang = lang.split('_')[0]
            if lang not in ('es', 'de', 'ca'):
                lang = 'en'
        else:
            lang = 'es'
        self.lang = lang

    def opts_to_config(self, config):
        for sec, val in self.sections.items():
            config[sec] = {}
            for s in val.keys():
                config[sec][s] = getattr(self, s)


# ---------------------------------------------------------------------------
# Colour map (populated by read_config / init_cfgcols)
# ---------------------------------------------------------------------------
cfgcols = {}


def init_cfgcols(colors=None):
    """Initialise the module colour map ``cfgcols`` from a {name: hex} dict.

    Defaults to :data:`default_colors`. Mirrors what ``read_config`` does after
    loading the user options.
    """
    global cfgcols
    src = colors if colors is not None else default_colors
    cfgcols = {k: ''.join(['#', v]) for k, v in src.items()}


def hex_to_rgb(h):
    """Convert a ``rrggbb`` hex string to an ``(r, g, b)`` tuple in 0..1."""
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return (r, g, b)


def _color(name):
    """Return the RGB tuple for a colour name from cfgcols (strips the '#')."""
    return hex_to_rgb(cfgcols[name][1:])


# ---------------------------------------------------------------------------
# read/reload config
# ---------------------------------------------------------------------------
def read_config(homedir):
    """Read ``<homedir>/cfg.ini`` and return a populated :class:`NexConf`.

    Writes the file back from defaults if it is missing or incomplete, matching
    the original behaviour. The returned object has every section's keys as
    attributes (overridden by file values where present).
    """
    global cfgcols
    from pathlib import Path
    cfgfile = Path(homedir) / 'cfg.ini'
    conf = configparser.ConfigParser()
    if cfgfile.exists():
        conf.read(cfgfile)
    popts = {}
    for k in conf.sections():
        popts.update(conf[k])

    if 'transits' in popts and not isinstance(popts['transits'], list):
        del popts['transits']

    opts = NexConf()
    opts.__dict__.update(popts)

    for keyc in default_colors.keys():
        val = getattr(opts, keyc)
        cfgcols[keyc] = ''.join(['#', val])

    if not cfgfile.exists() or len(opts.__dict__) != len(popts):
        opts.opts_to_config(conf)
        cfgfile.parent.mkdir(parents=True, exist_ok=True)
        with open(cfgfile, 'w') as fh:
            conf.write(fh)

    return opts


def reload_config(conf, boss):
    """Re-apply a config to the running app state.

    The ephemeris-path, favourites and orbs wiring depends on the ``boss`` /
    ``state`` / ``pysw`` layers that land in later milestones; for now this
    refreshes the options + colour map (the dependency-free part).
    """
    global cfgcols
    opts = boss.opts
    popts = {}
    for k in conf.keys():
        popts.update(conf[k])
    opts.__dict__.update(popts)

    for keyc in default_colors.keys():
        val = getattr(opts, keyc)
        cfgcols[keyc] = ''.join(['#', val])


# ---------------------------------------------------------------------------
# Colour parsers (consumed by zodiac.py / render)
# ---------------------------------------------------------------------------
def parse_aux_colors():
    auxcol = {}
    for cl in ('click1', 'click2', 'clicksoul', 'inv', 'low', 'transcol'):
        auxcol[cl] = _color(cl)
    return auxcol


def parse_zod_colors():
    return [_color(cl) for cl in ('fire', 'earth', 'air', 'water')]


def parse_plan_colors():
    return {cl: _color(cl) for cl in ('pers', 'tool', 'trans', 'node')}


def parse_asp_colors():
    return {cl: _color(cl) for cl in ('orange', 'green', 'blue', 'red')}


def reset_colors(opts):
    global cfgcols
    for keyc, val in default_colors.items():
        setattr(opts, keyc, val)
        cfgcols[keyc] = ''.join(['#', val])
