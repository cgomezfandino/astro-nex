# -*- coding: utf-8 -*-
import sys


def main():
    from .gui.app import AstroNexApp
    return AstroNexApp().run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
