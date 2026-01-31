"""Version information for Program Manager.

This is the single source of truth for the version number.
Update this file when releasing a new version.
"""

__version__ = "1.0.0"

VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0

VERSION_TUPLE = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)


def get_version() -> str:
    """Get the current version string."""
    return __version__


def get_version_tuple() -> tuple:
    """Get the current version as a tuple of integers."""
    return VERSION_TUPLE
