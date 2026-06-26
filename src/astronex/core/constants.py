# -*- coding: utf-8 -*-
"""Data tables extracted from legacy chart.py (lines ~12-24)."""

from math import sqrt, pi

PHI = 1 / ((1 + sqrt(5)) / 2)
RAD = pi / 180

points = [12, 12, 8, 8, 8, 8, 12, 6, 6, 6, 4]

planames = [
    'sun', 'moon', 'mercury', 'venus', 'mars',
    'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'node',
]

zodnames = [
    'aries', 'tauro', 'geminis', 'cancer', 'leo', 'virgo',
    'libra', 'scorpio', 'sagitario', 'capricornio', 'acuario', 'piscis',
]

aspnames = [
    'conj', 'semi', 'sext', 'cuad', 'trig', 'quinc',
    'opos', 'quinc', 'trig', 'cuad', 'sext', 'semi',
]

conj_class = [
    [
        (0, 4), (0, 6), (0, 9), (3, 4), (3, 9), (4, 6),
        (4, 7), (4, 8), (4, 9), (6, 7), (7, 9),
    ],
    [
        (0, 1), (0, 3), (0, 5), (0, 7), (0, 8), (1, 3),
        (1, 5), (1, 6), (2, 6), (2, 7), (3, 5), (3, 6),
        (3, 9), (5, 7), (5, 9), (6, 8), (6, 9),
    ],
    [
        (0, 2), (1, 2), (1, 4), (1, 7), (1, 8), (1, 9),
        (2, 3), (2, 4), (2, 5), (2, 8), (2, 9), (3, 7),
        (4, 5), (5, 6), (5, 8), (7, 8), (8, 9),
    ],
]

plan_class = [[0, 4, 9], [3, 6, 7], [1, 2, 5, 8]]

planclass = [0, 0, 1, 1, 2, 1, 2, 3, 3, 3, 4]  # related to
aspclass = [4, 0, 1, 2, 3, 1, 4, 1, 3, 2, 1, 0]  # orbs table

# Default orb table indexed orbs[planclass][aspclass]. In the legacy app this
# table was populated at runtime by config; this provides a standalone default
# so Chart.aspects() works without the config layer. Rows are planet classes
# (lum, normal, short, far, useless); columns are aspect orb classes.
DEFAULT_ORBS = [
    [3.0, 5.0, 6.0, 8.0, 9.0],   # lum
    [2.0, 4.0, 5.0, 6.0, 7.0],   # normal
    [1.5, 3.0, 4.0, 5.0, 6.0],   # short
    [1.0, 2.0, 3.0, 4.0, 5.0],   # far
    [1.0, 2.0, 2.0, 3.0, 4.0],   # useless
]
