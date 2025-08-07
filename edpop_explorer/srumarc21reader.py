from typing import List, Optional
from abc import abstractmethod, ABC

from edpop_explorer import SRUReader, BIBLIOGRAPHICAL
from edpop_explorer.marc21 import Marc21Data, Marc21Field, translation_dictionary, Marc21BibliographicalReaderMixin, \
    Marc21BibliographicalRecord


class SRUMarc21Reader(SRUReader):
    '''Subclass of ``SRUReader`` that adds Marc21 functionality.

    This class is still abstract and to create concrete readers
    the ``_get_link()``, ``_get_identifier()`` 
    and ``_convert_record`` methods should be implemented.

    .. automethod:: _convert_record
    .. automethod:: _get_link
    .. automethod:: _get_identifier'''
    marcxchange_prefix: str = ''
    picaxml_prefix: str = 'info:srw/schema/5/picaXML-v1.0:'

    @classmethod
    def _get_subfields(cls, sruthifield, ns_prefix: str = None) -> list:
        # If there is only one subfield, sruthi puts it directly in
        # a dict, otherwise it uses a list of dicts. Make sure that
        # we always have a list.
        subfielddata = sruthifield[f'{ns_prefix}subfield']
        if isinstance(subfielddata, dict):
            sruthisubfields = [subfielddata]
        else:
            sruthisubfields = subfielddata
        assert isinstance(sruthisubfields, list)
        return sruthisubfields

    @classmethod
    def _convert_to_marc21data(cls, sruthirecord: dict) -> Marc21Data:
        data = Marc21Data()
        data.raw = sruthirecord
        # marcxml (marc21 in xml) consists of a controlfield and a datafield.
        # The controlfield and the datafield contain multiple fields.
        # The controlfield consists of simple pairs of tags (field numbers)
        # and texts (field values).
        for sruthicontrolfield in \
                sruthirecord[f'{cls.marcxchange_prefix}controlfield']:
            tag = sruthicontrolfield['tag']
            text = sruthicontrolfield['text']
            data.controlfields[tag] = text
        # The datafield is more complex; these fields also have two indicators,
        # one-digit numbers that carry special meanings, and multiple subfields
        # that each have a one-character code.
        for sruthifield in sruthirecord[f'{cls.marcxchange_prefix}datafield']:
            fieldnumber = sruthifield['tag']
            field = Marc21Field(
                fieldnumber=fieldnumber,
                indicator1=sruthifield['ind1'],
                indicator2=sruthifield['ind2'],
                subfields={}
            )
            # The translation_dictionary contains descriptions for a number
            # of important fields. Include them so that the user can more
            # easily understand the record.
            if fieldnumber in translation_dictionary:
                field.description = translation_dictionary[fieldnumber]
            sruthisubfields = cls._get_subfields(sruthifield, ns_prefix=cls.marcxchange_prefix)

            for sruthisubfield in sruthisubfields:
                field.subfields[sruthisubfield['code']] = \
                    sruthisubfield['text']
            data.fields.append(field)
        # Finally, include the fields of the PicaXML of the record,
        # if available.
        if pica_data := sruthirecord.get(f'{cls.picaxml_prefix}datafield'):
            for sruthifield in pica_data:
                fieldnumber = sruthifield['tag']
                field = Marc21Field(
                    fieldnumber=fieldnumber,
                    subfields={}
                )
                sruthisubfields = cls._get_subfields(sruthifield, ns_prefix=cls.picaxml_prefix)
                for sruthisubfield in sruthisubfields:
                    try:
                        text = sruthisubfield.get('text')
                        field.subfields[sruthisubfield['code']] = text
                    except KeyError:
                        pass  # Code should be present, but don't crash if not
                data.picafields.append(field)
        return data
    
    @classmethod
    @abstractmethod
    def _get_link(cls, data: Marc21Data) -> Optional[str]:
        '''Get a public URL according to the Marc21 data or ``None`` if it
        is not available.'''
        pass

    @classmethod
    @abstractmethod
    def _get_identifier(cls, data: Marc21Data) -> Optional[str]:
        '''Get the unique identifier from the Marc21 data or ``None`` if it
        is not available.'''
        pass





class SRUMarc21BibliographicalReader(SRUMarc21Reader, Marc21BibliographicalReaderMixin, ABC):
    '''Subclass of ``SRUMarc21Reader`` that adds functionality to create
    instances of ``BibliographicRecord``.

    This subclass assumes that the Marc21 data is according to the standard
    format of Marc21 for bibliographical data. See:
    https://www.loc.gov/marc/bibliographic/
    '''

    records: List[Marc21BibliographicalRecord]
    READERTYPE = BIBLIOGRAPHICAL
    
    @classmethod
    def _convert_record(cls, raw_data: dict) -> Marc21BibliographicalRecord:
        data = cls._convert_to_marc21data(raw_data)
        return cls._marc21data_to_record(data)

