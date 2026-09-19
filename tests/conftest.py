import os
from pathlib import Path

dogwood = Path(__file__).resolve().parents[1] / ".tools" / "dogwood"
if "HIRZ_DOGWOOD" not in os.environ and dogwood.exists():
    os.environ["HIRZ_DOGWOOD"] = str(dogwood)
