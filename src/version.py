"""
Version information for Mitotic Spindle Tool

This is the single source of truth for version information.
All other files should import from here.
"""

__version__ = "1.1.4"
__version_info__ = tuple(map(int, __version__.split('.')))

# For display purposes (with 'v' prefix)
VERSION_DISPLAY = f"v{__version__}"

# For compatibility with older code
version = __version__