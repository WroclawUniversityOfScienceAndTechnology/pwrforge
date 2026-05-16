from typing import Optional

from pwrforge.config import Pic18Config


def create_pic18_config(chip: Optional[str]) -> Optional[Pic18Config]:
    if chip is None:
        return None
    return Pic18Config(chip=chip.upper())
