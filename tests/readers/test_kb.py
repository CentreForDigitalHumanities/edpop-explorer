from edpop_explorer.readers.kb import KBReader

record_identifier_key = 'http://krait.kb.nl/coop/tel/handbook/telterms.html:recordIdentifier'


def test_find_ppn_ri_picarta():
    data = {
        record_identifier_key: 'http://picarta.pica.nl/DB=2.4/PPN?PPN=306044579'
    }
    reader = KBReader()
    assert reader._find_ppn(data) == '306044579'


def test_find_ppn_ri_picarta_with_x():
    data = {
        record_identifier_key: 'http://picarta.pica.nl/DB=2.4/PPN?PPN=28961774X'
    }
    reader = KBReader()
    assert reader._find_ppn(data) == '28961774X'


def test_find_ppn_ri_oclc():
    data = {
        record_identifier_key: 'https://opc-kb.oclc.org/DB=1/PPN?PPN=238713652'
    }
    reader = KBReader()
    assert reader._find_ppn(data) == '238713652'
