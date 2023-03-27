import cmd2
from typing import List, Optional, Type

from edpop_explorer.apireader import APIReader, APIRecord, APIException
from edpop_explorer.readers.hpb import HPBReader
from edpop_explorer.readers.vd import VD16Reader, VD17Reader, VD18Reader
from edpop_explorer.readers.cerl_thesaurus import CERLThesaurusReader
from edpop_explorer.readers.gallica import GallicaReader
from edpop_explorer.readers.stcn import STCNReader
from edpop_explorer.readers.sbtireader import SBTIReader


class EDPOPXShell(cmd2.Cmd):
    intro = 'Welcome to the EDPOP explorer! Type ‘help’ for help.\n'
    prompt = '[edpop-explorer] # '
    reader: APIReader = None
    shown: int = 0
    RECORDS_PER_PAGE = 10

    def do_next(self, args) -> None:
        if self.reader is None:
            self.perror('First perform an initial search')
        elif self.shown >= self.reader.number_of_results:
            self.perror('All records have been shown')
        else:
            if self.reader.number_fetched - self.shown < self.RECORDS_PER_PAGE:
                self.reader.fetch_next()
            self.shown += self._show_records(self.reader.records,
                                             self.shown,
                                             self.RECORDS_PER_PAGE)

    def do_show(self, args) -> None:
        if self.reader is None:
            self.perror('First perform an initial search')
            return None
        try:
            # TODO: consider using argparse
            index = int(args) - 1
        except (TypeError, ValueError):
            self.perror('Please provide a valid number')
            return None
        try:
            self.poutput(self.reader.records[index].show_record())
        except IndexError:
            self.perror('Please provide a record number that has been loaded')

    def do_hpb(self, args) -> None:
        'CERL\'s Heritage of the Printed Book Database'
        self._query(HPBReader, args)

    def do_vd16(self, args) -> None:
        """Verzeichnis der im deutschen Sprachbereich erschienenen Drucke
        des 16. Jahrhunderts"""
        self._query(VD16Reader, args)

    def do_vd17(self, args) -> None:
        """Verzeichnis der im deutschen Sprachbereich erschienenen Drucke
        des 17. Jahrhunderts"""
        self._query(VD17Reader, args)

    def do_vd18(self, args) -> None:
        """Verzeichnis der im deutschen Sprachbereich erschienenen Drucke
        des 18. Jahrhunderts"""
        self._query(VD18Reader, args)

    def do_gallica(self, args) -> None:
        'Gallica'
        self._query(GallicaReader, args)

    def do_ct(self, args) -> None:
        'CERL Thesaurus'
        self._query(CERLThesaurusReader, args)

    def do_stcn(self, args) -> None:
        'Short Title Catalogue Netherlands'
        self._query(STCNReader, args)

    def do_sbti(self, args) -> None:
        'Scottish Book Trade Index'
        self._query(SBTIReader, args)

    def _show_records(self, records: List[APIRecord],
                      start: int,
                      limit: Optional[int] = None) -> int:
        """Show the records from start, with limit as the maximum number
        of records to show. Return the number of records shown."""
        total = len(records)
        remaining = total - start
        if remaining < 1:
            return 0
        # Determine count (the number of items to show)
        if limit is None:
            count = limit
        else:
            count = min(remaining, limit)
        digits = len(str(total))
        for i in range(start, start + count):
            print('{:{digits}} - {}'.format(
                i + 1, records[i].get_title(), digits=digits
            ))
        return count

    def _query(self, readerclass: Type[APIReader], query: str):
        self.reader = readerclass()
        self.shown = 0
        try:
            self.reader.prepare_query(query)
            self.pfeedback(
                'Performing query: {}'.format(self.reader.prepared_query)
            )
            self.reader.fetch()
        except APIException as err:
            self.perror('Error while fetching results: {}'.format(err))
            self.reader = None
            self.shown = 0
            return
        self.pfeedback(
            '{} records found.'.format(self.reader.number_of_results)
        )
        self.shown += self._show_records(
            self.reader.records, self.shown, self.RECORDS_PER_PAGE
        )