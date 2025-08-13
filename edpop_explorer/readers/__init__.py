'''This package contains concrete subclasses of ``Reader``.'''

__all__ = [
    "BnFReader",
    "CERLThesaurusReader",
    "FBTEEReader",
    "GallicaReader",
    "HPBReader",
    "KBReader",
    "SBTIReader",
    "VD16Reader",
    "VD17Reader",
    "VD18Reader",
    "VDLiedReader",
    "STCNReader",
    "STCNPersonsReader",
    "STCNPrintersReader",
    "USTCReader",
    "KVCSReader",
    "DutchAlmanacsReader",
    "PierreBelleReader",
    "ESTCReader",
    "get_record_by_uri",
    "ALL_READERS",
]

from edpop_explorer import Reader

from .bnf import BnFReader
from .cerl_thesaurus import CERLThesaurusReader
from .fbtee import FBTEEReader
from .gallica import GallicaReader
from .hpb import HPBReader
from .kb import KBReader
from .sbti import SBTIReader
from .stcn import STCNReader, STCNPersonsReader, STCNPrintersReader
from .ustc import USTCReader
from .vd import VD16Reader, VD17Reader, VD18Reader, VDLiedReader
from .kvcs import KVCSReader
from .dutch_almanacs import DutchAlmanacsReader
from .pierre_belle import PierreBelleReader
from .estc import ESTCReader
from .utils import get_record_by_uri

import sys
from typing import List, Type


def _get_all_readers() -> List[Type[Reader]]:
    """Create a list of all reader classes included in this package."""
    all_names = __all__.copy()
    all_readers: List[Type[Reader]] = []
    for name in all_names:
        cls = getattr(sys.modules[__name__], name, None)
        if isinstance(cls, type) and issubclass(cls, Reader):
            all_readers.append(cls)
    return all_readers

ALL_READERS = _get_all_readers()

