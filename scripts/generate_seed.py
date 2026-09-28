#!/usr/bin/env python3
import json
from pathlib import Path


def main():
    seed_dir = Path(__file__).parent.parent / "data" / "seed"
    incidents_path = seed_dir / "incidents.json"
    deploys_path = seed_dir / "deploys.json"

    assert incidents_path.exists(), f"Missing {incidents_path}"
    assert deploys_path.exists(), f"Missing {deploys_path}"

    with open(incidents_path, "r") as f:
        incidents = json.load(f)

    with open(deploys_path, "r") as f:
        deploys = json.load(f)

    print(f"Verified seed data: {len(incidents)} incidents, {len(deploys)} deploys.")

if __name__ == "__main__":
    main()
