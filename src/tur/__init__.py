from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version('tur')
except PackageNotFoundError:
    __version__ = '0.12.1'
