"""Shared pytest setup. Does not open Neon or MongoDB."""

import os

# Session tests need a key. Production still refuses to invent one.
os.environ.setdefault("SECRET_KEY", "test-only-not-for-production")
