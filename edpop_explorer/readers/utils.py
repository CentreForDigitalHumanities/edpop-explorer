from typing import Optional

from edpop_explorer import Field


def format_holding(institution_name: Optional[str], shelfmark: Optional[str]) -> Optional[Field]:
    content = ' / '.join(filter(None, [institution_name, shelfmark]))
    if not content:
        return None
    return Field(content)
