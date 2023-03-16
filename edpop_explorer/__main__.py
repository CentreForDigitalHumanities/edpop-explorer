from typing import Dict, List, Optional, Any
import readline  # noqa: F401
import math
from appdirs import AppDirs
from termcolor import colored, cprint
from pathlib import Path

from edpop_explorer.apireader import APIReader, APIRecord, APIException
from edpop_explorer.readers.hpb import HPBReader
from edpop_explorer.readers.vd import VD16Reader, VD17Reader, VD18Reader
from edpop_explorer.readers.cerl_thesaurus import CERLThesaurusReader
from edpop_explorer.readers.gallica import GallicaReader
from edpop_explorer.readers.stcn import STCNReader


try:
    from colorama import just_fix_windows_console
    just_fix_windows_console()
except ImportError:
    pass

historyfile = Path(AppDirs('edpop-explorer', 'cdh').user_data_dir) / 'history'

RECORDS_PER_PAGE = 10


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
    'gallica': {
        'help': 'Gallica',
        'reader': GallicaReader
    },
    'ct': {
        'help': 'CERL Thesaurus',
        'reader': CERLThesaurusReader
    },
    'stcn': {
        'help': 'Short Title Catalogue Netherlands',
        'reader': STCNReader
    },
    'show': {
        'help': 'Show details of a given entry. Usage: show <entry-number>',
        'reader': None
    },
    'next': {
        'help': f'Fetch and show next {RECORDS_PER_PAGE} entries',
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


def save_history() -> None:
    if not historyfile.parent.exists():
        historyfile.parent.mkdir(parents=True)
    readline.write_history_file(historyfile)


def show_records(records: List[APIRecord],
                 start: int,
                 limit: Optional[int] = None) -> int:
    """Show the records from start, with limit as the maximum number of records
    to show. Return the number of records shown."""
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


def main() -> None:
    cprint(
        'Welcome to the EDPOP explorer!\n'
        'Available commands: {}\nType ‘help’ for help.'
        .format(', '.join(readercommands)), 'yellow', attrs=['bold']
    )
    reader: APIReader = None
    shown: int = 0
    if historyfile.exists():
        readline.read_history_file(historyfile)
    while True:
        try:
            line = input(colored('# ', attrs=['bold']))
        except EOFError:
            save_history()
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
            save_history()
            break
        elif command == 'next':
            if reader is None:
                error('First perform an initial search')
            elif shown >= reader.number_of_results:
                error('All records have been shown')
            else:
                if reader.number_fetched - shown < RECORDS_PER_PAGE:
                    reader.fetch_next()
                shown += show_records(reader.records, shown, RECORDS_PER_PAGE)
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
        # All other commands are mapped to one of the readers
        elif command in readercommands:
            if not argument:
                error('{} command expects an argument.'.format(command))
                continue
            readerclass = readercommands[command]['reader']
            # Invoke constructor of readerclass
            reader = readerclass()
            shown = 0
            try:
                reader.prepare_query(argument)
                success('Performing query: {}'.format(reader.prepared_query))
                reader.fetch()
            except APIException as err:
                error('Error while fetching results: {}'.format(err))
                reader = None
                continue
            success('{} records found.'.format(reader.number_of_results))
            shown += show_records(reader.records, shown, RECORDS_PER_PAGE)
        else:
            error('Command does not exist: {}'.format(command))


if __name__ == '__main__':
    main()
