#!/usr/bin/env python3

import os
import shutil
import sys

CFG_TEMPLATE = "release/config.json-template"
DEV_CONFIG = "data/dev-config.json"

# Work either as `python3 -m scripts.dev-install` or `python3 scripts/dev-install.py`
ROOT = os.path.abspath(f"{os.path.dirname(os.path.abspath(__file__))}/..")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from imports import json  # load_json/save_json helpers


def dev_install():
    if not os.path.isfile(CFG_TEMPLATE):
        print(f"ERROR: Config template not found: {CFG_TEMPLATE}", file=sys.stderr)
        print("       Ensure running install from top level", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(DEV_CONFIG), exist_ok=True)

    if not os.path.isfile(DEV_CONFIG):
        shutil.copyfile(CFG_TEMPLATE, DEV_CONFIG)
        print(f"INFO: Created {DEV_CONFIG} from {CFG_TEMPLATE}")

    user = os.getlogin()
    if not user:
        print("ERROR: Could not determine current user to add to admins", file=sys.stderr)
        return 1

    config = json.load_json(DEV_CONFIG)
    admins = config.get("admins")
    if user not in admins:
        admins.append(user)
        json.save_json(DEV_CONFIG, config)
        print(f"INFO: Added {user!r} to dev admin list")
    else:
        print(f"INFO: {user!r} already in dev admin list")

    return 0


if __name__ == "__main__":
    raise SystemExit(dev_install())

