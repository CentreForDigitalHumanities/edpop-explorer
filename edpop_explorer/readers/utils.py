from typing import Optional

from edpop_explorer import Field, Reader, Record


def format_holding(institution_name: Optional[str], shelfmark: Optional[str]) -> Optional[Field]:
    content = ' / '.join(filter(None, [institution_name, shelfmark]))
    if not content:
        return None
    return Field(content)


def get_record_by_uri(record_uri: str, readers: list[type[Reader]]) -> Optional[Record]:
    """Get a record by its URI using all given readers."""
    for reader in readers:
        if record_uri.startswith(reader.IRI_PREFIX):
            return reader.get_by_iri(record_uri)
    return None
