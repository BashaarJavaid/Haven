"""Static action catalog; dynamic risk scoring belongs to item 8."""

from importlib.resources import files
from typing import TypedDict, cast

import yaml


class Profile(TypedDict):
    impact: int
    reversibility: str
    band: str


CLASSES = cast(
    dict[str, Profile],
    yaml.safe_load(files(__package__).joinpath("classes.yaml").read_text()),
)
