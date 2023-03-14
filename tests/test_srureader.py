import unittest
from unittest.mock import patch
import json
from pathlib import Path

from edpop_explorer.srumarc21reader import SRUMarc21Reader


TESTDATA = json.load(open(Path(__file__).parent / 'TESTDATA', 'r'))


class SRUReaderTestCase(unittest.TestCase):
    @patch('edpop_explorer.srureader.sruthi')
    def test_fetch(self, mock_sruthi):
        mock_sruthi.searchretrieve.return_value = TESTDATA
        reader = SRUMarc21Reader()
        reader.transform_query = lambda x: x
        reader.get_link = lambda x: x
        reader.sru_url = ''
        reader.sru_version = '1.1'
        reader.prepare_query('testquery')
        reader.fetch()
        results = reader.records
        # Field with multiple subfields
        self.assertEqual(
            results[0].get_first_field('245').subfields['a'],
            'Aeschylus: Eumenides.'
        )
        # Field with a single subfield
        self.assertEqual(
            results[0].get_first_field('650').subfields['a'],
            'Aeschylus Eumenides.'
        )
        # Field's description
        self.assertEqual(
            results[0].get_first_field('650').description,
            'Subject Added Entry - Topical Term'
        )
        # Field that occurs multiple times
        self.assertEqual(
            len(results[0].get_fields('500')),
            5
        )
