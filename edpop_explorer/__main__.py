from typing import Dict, List, Optional
import readline
import math

from edpop_explorer.apireader import APIReader, APIRecord, APIException
from edpop_explorer.readers.hpb import HPBReader
from edpop_explorer.readers.vd import VD16Reader, VD17Reader, VD18Reader
from edpop_explorer.readers.stcn import STCNReader


readercommands: Dict[str, APIReader] = {
    'hpb': HPBReader,
    'vd16': VD16Reader,
    'vd17': VD17Reader,
    'vd18': VD18Reader,
    'stcn': STCNReader
}


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
    print(
        'Welcome to the EDPOP explorer!\n'
        'Available commands: {}, next, show, exit'
        .format(', '.join(readercommands))
    )
    reader: APIReader = None
    shown: int = 0
    while True:
        try:
            line = input('# ')
        except EOFError:
            break
        except KeyboardInterrupt:
            print('')
            continue
        if line.strip() != '':
            command, *arguments = line.split()
        else:
            continue
        if command == 'exit':
            break
        elif command in readercommands:
            if len(arguments) != 1:
                print('{} command expects one argument.'.format(command))
                continue
            readerclass = readercommands[command]
            # Invoke constructor of readerclass
            reader = readerclass()
            shown = 0
            try:
                reader.fetch(arguments[0])
            except APIException as err:
                print('Error while fetching results: {}'.format(err))
                reader = None
            print('{} records found.'.format(reader.number_of_results))
            shown += show_records(reader.records, shown, 10)
        elif command == 'next':
            if reader is None:
                print('First perform an initial search')
            elif shown >= reader.number_of_results:
                print('All records have been shown')
            else:
                if reader.number_fetched - shown < 10:
                    reader.fetch_next()
                shown += show_records(reader.records, shown, 10)
        elif command == 'show':
            if reader is None:
                print('First perform an initial search')
                continue
            try:
                index = int(arguments[0]) - 1
            except (IndexError, ValueError):
                print('Please provide a valid number')
                continue
            try:
                print(reader.records[index].show_record())
            except IndexError:
                print('Please provide a record number that has been loaded')
        else:
            print('Command does not exist: {}'.format(command))


if __name__ == '__main__':
    main()
