
import bz2
import lzma
from types import ModuleType
import zlib


COMPRESSION_METHODS = {
    'bzip2': bz2,
    'gzip': zlib,
    'xz': lzma,
}


def compress(data: bytes, method_name: str) -> bytes:
    module = _get_compression_module(method_name)
    compressed = module.compress(data)
    assert isinstance(compressed, bytes)
    return compressed


def decompress(compressed: bytes, method_name: str) -> bytes:
    module = _get_compression_module(method_name)
    data = module.decompress(compressed)
    assert isinstance(data, bytes)
    return data


def _get_compression_module(name: str) -> ModuleType:
    """
    Return a compression module from the method name.
    """
    try:
        module = COMPRESSION_METHODS[name]
        return module
    except (KeyError, ValueError):
        # Unknown name.
        message = "Method '{}' unknown. Must be one of: {}".format(
            name, ', '.join(COMPRESSION_METHODS))
        raise KeyError(message)
