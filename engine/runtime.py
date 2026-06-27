"""Shared long-lived singletons."""
from __future__ import annotations

from .oracle import Oracle
from .osiris_intake import OsirisIntake

intake = OsirisIntake()
oracle = Oracle()
