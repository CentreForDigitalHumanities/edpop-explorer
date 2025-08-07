from edpop_explorer.readers.estc import _flatten_sections

def test_flatten_sections():
    data = {
        'section1': {
            '001': 'value1',
            '002': {
                'a': 'value2a',
                'b': 'value2b'
            }
        },
        'section2': {
            '003': 'value3'
        }
    }
    flattened = _flatten_sections(data)
    assert flattened == {
        '001': 'value1',
        '002': data['section1']['002'],
        '003': 'value3'
    }

def test_flatten_sections_empty():
    assert _flatten_sections({}) == {}
