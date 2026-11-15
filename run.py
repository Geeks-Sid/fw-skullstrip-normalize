#!/usr/bin/env python
"""The run script."""
from flywheel_gear_toolkit import GearToolkitContext

from fw_skullstrip_normalize.main import run

if __name__ == "__main__":  # pragma: no cover
    with GearToolkitContext() as gear_context:
        gear_context.init_logging()
        run(gear_context)
