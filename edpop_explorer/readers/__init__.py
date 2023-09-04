'''This package contains concrete subclasses of ``Reader``.'''

__all__ = [
    "BibliopolisReader",
    "BnFReader",
    "CERLThesaurusReader",
    "FBTEEReader",
    "GallicaReader",
    "HPBReader",
    "KBReader",
    "SBTIReader",
    "USTCReader",
    "VD16Reader",
    "VD17Reader",
    "VD18Reader",
    "VDLiedReader",
    "STCNReader",
    "USTCReader",
    "ALL_READERS",
]

from .bibliopolis import BibliopolisReader
from .bnf import BnFReader
from .cerl_thesaurus import CERLThesaurusReader
from .fbtee import FBTEEReader
from .gallica import GallicaReader
from .hpb import HPBReader
from .kb import KBReader
from .sbtireader import SBTIReader
from .stcn import STCNReader
from .ustc import USTCReader
from .vd import VD16Reader, VD17Reader, VD18Reader, VDLiedReader

import sys
from typing import List, Type


def _get_all_readers() -> List[Type]:
    """Create a list of all reader classes included in this package."""
    all_names = __all__.copy()
    all_names.pop()  # Remove "ALL_READERS" itself
    all_readers: List[str] = []
    for name in all_names:
        cls = getattr(sys.modules[__name__], name, None)
        if cls is not None:
            all_readers.append(cls)
    return all_readers

ALL_READERS = _get_all_readers()

