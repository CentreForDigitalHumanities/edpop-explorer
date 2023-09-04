import cmd2
import math
import yaml
from typing import List, Optional, Type
from pygments import highlight
from pygments.lexers import TurtleLexer
from pygments.lexers.data import YamlLexer
from pygments.formatters import Terminal256Formatter

from edpop_explorer import Reader, Record, ReaderError
from edpop_explorer.readers import (
    FBTEEReader,
    GallicaReader,
    BibliopolisReader,
    CERLThesaurusReader,
    HPBReader,
    VD16Reader,
    VD17Reader,
    VD18Reader,
    VDLiedReader,
    KBReader,
    STCNReader,
    SBTIReader,
    USTCReader,
    BnFReader,
)


class EDPOPXShell(cmd2.Cmd):
    intro = 'Welcome to the EDPOP explorer! Type ‘help’ for help.\n'
    prompt = '[edpop-explorer] # '
    reader: Optional[Reader] = None
    shown: int = 0
    RECORDS_PER_PAGE = 10

    def __init__(self):
        super().__init__()

        self.exact = False
        self.add_settable(cmd2.Settable(
            'exact', bool, 'use exact queries without preprocessing', self
        ))

    def get_record_from_argument(self, args) -> Optional[Record]:
        """Get the record requested by the user; show error message
        and return None if this fails"""
        if self.reader is None:
            self.perror('First perform an initial search')
            return
        try:
            # TODO: consider using argparse
            index = int(args) - 1
        except (TypeError, ValueError):
            self.perror('Please provide a valid number')
            return
        try:
            record = self.reader.records[index]
        except IndexError:
            self.perror('Please provide a record number that has been loaded')
            return
        return record

    def do_next(self, args) -> None:
        if self.reader is None:
            self.perror('First perform an initial search')
            return
        assert self.reader.number_of_results is not None
        assert self.reader.number_fetched is not None
        if self.shown >= self.reader.number_of_results:
            self.perror('All records have been shown')
        else:
            if self.reader.number_fetched - self.shown < self.RECORDS_PER_PAGE:
                self.reader.fetch_next()
            self.shown += self._show_records(self.reader.records,
                                             self.shown,
                                             self.RECORDS_PER_PAGE)

    def do_show(self, args) -> None:
        '''Show a normalized version of the record with the given number.'''
        record = self.get_record_from_argument(args)
        if record is None:
            return
        record.fetch()  # Necessary in case this is a lazy record
        self.poutput(cmd2.ansi.style_success(
            record, bold=True
        ))
        recordtype = str(record._rdf_class).rsplit('/',1)[1]
        self.poutput(f'Record type: {recordtype}')
        self.poutput
        if record.identifier:
            self.poutput(f'Identifier: {record.identifier}')
        if record.link:
            self.poutput('URL: ' + str(record.link))
        self.poutput(cmd2.ansi.style('Fields:', bold=True))
        for fieldname, _, _ in record._fields:
            fieldname_human = fieldname.capitalize().replace('_', ' ')
            # TODO: make a field iterator for Record
            value = getattr(record, fieldname)
            if value:
                if isinstance(value, list):
                    text = '\n' + '\n'.join([('  - ' + str(x)) for x in value])
                else:
                    text = str(value)
                self.poutput(
                    cmd2.ansi.style(f'- {fieldname_human}: ', bold=True) + text
                )

    def do_showrdf(self, args) -> None:
        '''Show an RDF representation of the record with the given number
        in Turtle format.'''
        record = self.get_record_from_argument(args)
        if record is None:
            return
        try:
            graph = record.to_graph()
            ttl = graph.serialize()
            highlighted = highlight(
                ttl, TurtleLexer(), Terminal256Formatter(style='vim')
            )
            self.poutput(highlighted)
        except ReaderError as err:
            self.perror('Cannot generate RDF: {}'.format(err))

    def do_showraw(self, args) -> None:
        '''Show the raw data of the record with the given number in the
        source catalog.'''
        record = self.get_record_from_argument(args)
        if record is None:
            return
        data = record.get_data_dict()
        yaml_data = yaml.dump(data, allow_unicode=True)
        highlighted = highlight(
            yaml_data, YamlLexer(), Terminal256Formatter(style='vim')
        )
        self.poutput(highlighted)

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

    def do_vdlied(self, args) -> None:
        """Verzeichnis der deutschsprachigen Liedflugschriften"""
        self._query(VDLiedReader, args)
    
    def do_bnf(self, args) -> None:
        """Bibliothèque nationale de France"""
        self._query(BnFReader, args)
    
    def do_gallica(self, args) -> None:
        'Gallica'
        self._query(GallicaReader, args)
    
    def do_bibliopolis(self, args) -> None:
        'Bibliopolis Personendatabase'
        self._query(BibliopolisReader, args)

    def do_ct(self, args) -> None:
        'CERL Thesaurus'
        self._query(CERLThesaurusReader, args)
    
    def do_stcn(self, args) -> None:
        'Short Title Catalogue Netherlands'
        self._query(STCNReader, args)
    
    def do_sbti(self, args) -> None:
        'Scottish Book Trade Index'
        self._query(SBTIReader, args)
    
    def do_fbtee(self, args) -> None:
        'French Book Trade in Enlightenment Europe'
        self._query(FBTEEReader, args)
    
    def do_ustc(self, args) -> None:
        'Universal Short Title Catalogue'
        self._query(USTCReader, args)
    
    def do_kb(self, args) -> None:
        'Koninklijke Bibliotheek'
        self._query(KBReader, args)

    def _show_records(self, records: List[Record],
                      start: int,
                      limit=math.inf) -> int:
        """Show the records from start, with limit as the maximum number
        of records to show. Return the number of records shown."""
        total = len(records)
        remaining = total - start
        if remaining < 1:
            return 0
        # Determine count (the number of items to show)
        count = int(min(remaining, limit))
        digits = len(str(total))
        for i in range(start, start + count):
            print('{:{digits}} - {}'.format(
                i + 1, str(records[i]), digits=digits
            ))
        return count

    def _query(self, readerclass: Type[Reader], query: str):
        self.reader = readerclass()
        self.shown = 0
        try:
            if not self.exact:
                self.reader.prepare_query(query)
                self.pfeedback(
                    'Performing query: {}'.format(self.reader.prepared_query)
                )
            else:
                self.reader.set_query(query)
                self.pfeedback(
                    'Performing exact query: {}'.format(query)
                )
            self.reader.fetch()
        except ReaderError as err:
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
