"""Entry point to run tests via `python3 -m tests`."""

from __future__ import annotations

import sys
from tests.run_tests import main

if __name__ == "__main__":
    sys.exit(main())
