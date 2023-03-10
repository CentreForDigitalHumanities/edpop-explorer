from typing import Dict, List, Optional, Any
import readline  # noqa: F401
import math
from termcolor import colored, cprint

from edpop_explorer.apireader import APIReader, APIRecord, APIException
from edpop_explorer.readers.hpb import HPBReader
from edpop_explorer.readers.vd import VD16Reader, VD17Reader, VD18Reader
from edpop_explorer.readers.cerl_thesaurus import CERLThesaurusReader
from edpop_explorer.readers.stcn import STCNReader


readercommands: Dict[str, Dict[str, Any]] = {
    'hpb': {
        'help': 'Heritage of the Printed Book Database',
        'reader': HPBReader
    },
    'vd16': {
        'help': 'Verzeichnis der im deutschen Sprachbereich erschienenen Drucke des 16. Jahrhunderts',
        'reader': VD16Reader
    },
    'vd17': {
        'help': 'Verzeichnis der im deutschen Sprachbereich erschienenen Drucke des 17. Jahrhunderts',
        'reader': VD17Reader
    },
    'vd18': {
        'help': 'Verzeichnis der im deutschen Sprachbereich erschienenen Drucke des 18. Jahrhunderts',
        'reader': VD18Reader
    },
    'ct': {
        'help': 'CERL Thesaurus',
        'reader': CERLThesaurusReader
    },
    'show': {
        'help': 'Show details of a given entry. Usage: show <entry-number>',
        'reader': None
    },
    'next': {
        'help': 'Fetch and show next 10 entries',
        'reader': None
    },
    'help': {
        'help': 'Show help about commands',
        'reader': None
    },
    'exit': {
        'help': 'Exit this programme',
        'reader': None
    },
}


def success(message: str) -> None:
    cprint(message, 'green', attrs=['bold'])


def error(message: str) -> None:
    cprint(message, 'red', attrs=['bold'])


def show_records(records: List[APIRecord],
                 start: int,
                 limit: Optional[int] = None) -> int:
    """Show the records from start, with limit as the maximum number of records
    to show. Return the number of records shown."""
    if len(records) == 0:
        return 0
    if limit is None or limit > len(records) - start:
        limit = len(records) - start
    digits = int(math.log10(len(records))) + 1
    i = start
    while i < (start + limit):
        print('{:{digits}} - {}'.format(
            i + 1, records[i].get_title(), digits=digits
        ))
        i += 1
    return i - start


def main() -> None:
    cprint(
        'Welcome to the EDPOP explorer!\n'
        'Available commands: {}\nType ‘help’ for help.'
        .format(', '.join(readercommands)), 'yellow', attrs=['bold']
    )
    reader: APIReader = None
    shown: int = 0
    while True:
        try:
            line = input(colored('# ', attrs=['bold']))
        except EOFError:
            break
        except KeyboardInterrupt:
            print('')
            continue
        if line.strip() != '':
            try:
                command, argument = line.split(maxsplit=1)
            except ValueError:
                command, argument = line, None
        else:
            continue
        if command == 'exit':
            break
        elif command == 'next':
            if reader is None:
                error('First perform an initial search')
            elif shown >= reader.number_of_results:
                error('All records have been shown')
            else:
                if reader.number_fetched - shown < 10:
                    reader.fetch_next()
                shown += show_records(reader.records, shown, 10)
        elif command == 'show':
            if reader is None:
                error('First perform an initial search')
                continue
            try:
                index = int(argument) - 1
            except (TypeError, ValueError):
                error('Please provide a valid number')
                continue
            try:
                print(reader.records[index].show_record())
            except IndexError:
                error('Please provide a record number that has been loaded')
        elif command == 'help':
            for cmd in readercommands:
                print('{}: {}'.format(cmd, readercommands[cmd]['help']))
        elif command in readercommands:
            if not argument:
                error('{} command expects an argument.'.format(command))
                continue
            readerclass = readercommands[command][reader]
            # Invoke constructor of readerclass
            reader = readerclass()
            shown = 0
            try:
                reader.fetch(argument)
            except APIException as err:
                error('Error while fetching results: {}'.format(err))
                reader = None
                continue
            success('{} records found.'.format(reader.number_of_results))
            shown += show_records(reader.records, shown, 10)
        else:
            error('Command does not exist: {}'.format(command))


if __name__ == '__main__':
    main()
