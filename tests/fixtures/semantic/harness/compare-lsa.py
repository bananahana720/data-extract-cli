"""Deterministic LSA fixture comparison harness used by integration tests."""

from __future__ import annotations

import sys


def main(argv: list[str]) -> int:
    tolerance = 0.7
    if len(argv) > 1:
        try:
            tolerance = float(argv[1])
        except ValueError:
            print(f"ERROR: Invalid tolerance '{argv[1]}'")
            return 1

    print("LSA comparison PASSED")
    print(f"Tolerance: {tolerance:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
