"""feature function for pwrforge"""

from pwrforge import __version__
from pwrforge.logger import get_logger

logger = get_logger()


def pwrforge_version() -> None:
    logger.info(f"pwrforge version: {__version__}")
