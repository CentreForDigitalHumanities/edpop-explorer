from unittest.mock import patch
import json
from pathlib import Path
from typing import Optional

from edpop_explorer import SRUMarc21BibliographicalReader, Marc21Data


TESTDATA = json.load(open(Path(__file__).parent / 'TESTDATA', 'r'))


class MockReader(SRUMarc21BibliographicalReader):
    def transform_query(self, query: str) -> str:
        return query

    @classmethod
    def _get_link(cls, data: Marc21Data) -> Optional[str]:
        return "https://www.example.com"

    @classmethod
    def _get_identifier(cls, data: Marc21Data) -> Optional[str]:
        return 'id'


class TestSRUMarc21BibliographicalReader:
    @patch('edpop_explorer.srureader.sruthi')
    def test_fetch(self, mock_sruthi):
        mock_sruthi.searchretrieve.return_value = TESTDATA
        reader = MockReader()
        reader.sru_url = ''
        reader.sru_version = '1.1'
        reader.prepare_query('testquery')
        reader.fetch()
        results = reader.records
        # Field with multiple subfields
        data = results[0].data
        assert data is not None
        firstfield = data.get_first_field('245')
        assert firstfield is not None
        assert firstfield.subfields['a'] == \
            'Aeschylus: Eumenides.'
        # Field with a single subfield
        firstfield = data.get_first_field('650')
        assert firstfield is not None
        assert firstfield.subfields['a'] == \
            'Aeschylus Eumenides.'
        # Field's description
        assert firstfield.description == \
            'Subject Added Entry - Topical Term'
        # Field that occurs multiple times
        assert len(data.get_fields('500')) == 5
        # Control field
        assert data.controlfields['007'] == 'tu'
