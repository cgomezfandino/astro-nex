# -*- coding: utf-8 -*-
"""Console entry point: ``python -m astronex`` / the ``astronex`` script.

The GTK import is deferred inside :func:`main` so this module can be imported
headlessly (e.g. by the test suite) without requiring a display.
"""
import sys


def main():
    """Launch the GTK 3 application; returns the process exit code."""
    from .gui.app import AstroNexApp
    return AstroNexApp().run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
