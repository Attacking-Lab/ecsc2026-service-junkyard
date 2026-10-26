import ctypes
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
# precomputed by "go run . build-index" (see build.sh / Dockerfile)
DEFAULT_INDEX_PATH = os.environ.get('SPELLCHECKER_INDEX', os.path.join(_DIR, 'dictionaries.idx'))

_lib = ctypes.CDLL(os.path.join(_DIR, 'libspellchecker.so'))
_lib.LoadIndex.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
_lib.LoadIndex.restype = ctypes.c_int
_lib.SpellcheckC.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_double, ctypes.POINTER(ctypes.c_void_p)]
_lib.SpellcheckC.restype = ctypes.c_int
_lib.HasDictionaries.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
_lib.HasDictionaries.restype = ctypes.c_int
_lib.FreeString.argtypes = [ctypes.c_void_p]
_lib.FreeString.restype = None

_index_loaded = False


def _take_string(out: ctypes.c_void_p) -> str:
    """Copy a string returned by the library and free it."""
    assert out.value is not None
    try:
        return ctypes.string_at(out.value).decode()
    finally:
        _lib.FreeString(out)


def load_index(path: str = DEFAULT_INDEX_PATH) -> None:
    """Map the precomputed dictionary index (takes < 1 ms, loading the same path again is a no-op).
    Not fork-safe: never import this module or call into the library before forking."""
    global _index_loaded
    out = ctypes.c_void_p()
    if _lib.LoadIndex(path.encode(), ctypes.byref(out)) != 0:
        raise RuntimeError(_take_string(out))
    _index_loaded = True


def ensure_dictionaries_loaded(languages: list[str]) -> None:
    """Load the index if necessary and check that it contains all languages."""
    if not _index_loaded:
        load_index()
    out = ctypes.c_void_p()
    if _lib.HasDictionaries('\n'.join(languages).encode(), ctypes.byref(out)) != 0:
        raise RuntimeError(_take_string(out))


def ensure_dictionary_loaded(language: str) -> None:
    ensure_dictionaries_loaded([language])


def Spellcheck(text: str, language: str, confidence: float = 1.0) -> str:
    if not _index_loaded:
        load_index()
    out = ctypes.c_void_p()
    status = _lib.SpellcheckC(text.encode(), language.encode(), confidence, ctypes.byref(out))
    result = _take_string(out)
    if status != 0:
        raise RuntimeError(result)
    return result
