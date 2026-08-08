#!/usr/bin/env python3

"""Convenience wrapper so the app can be run from a source checkout.

The real entry point is leaf_calculator.cli:main, which is also what the
installed `nissan-leaf-calculator` console script calls.
"""

from leaf_calculator.cli import main

if __name__ == "__main__":
    main()
