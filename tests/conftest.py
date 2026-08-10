# Copyright (C) 2026 by Max R. P. Grossmann <m@max.pm>
# SPDX-License-Identifier: 0BSD

"""Hypothesis settings profiles.

Local runs stay fast; CI trades time for many more random markets, and
turns off the per-example deadline so that a slow shared runner cannot
produce a spurious failure. Select with `--hypothesis-profile`, which CI
passes explicitly.
"""

from hypothesis import HealthCheck, settings

settings.register_profile("dev", max_examples=200)
settings.register_profile(
    "ci",
    max_examples=5000,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("dev")
