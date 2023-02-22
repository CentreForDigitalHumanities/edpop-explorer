from typing import Dict, List, Optional
import readline
import math

from apireader import APIReader, APIRecord
from readers.hpb import HPBReader


readercommands: Dict[str, APIReader] = {
    'hpb': HPBReader,
}


def show_records(records: List[APIRecord],
                 start: int,
                 end: Optional[int] = None) -> None:
    if len(records) == 0:
        return
    if end is None:
        end = len(records)
    digits = int(math.log10(len(records))) + 1
    i = start
    while i < end:
        print('{:{digits}} - {}'.format(
            i + 1, records[i].get_title(), digits=digits
        ))
        i += 1


def main() -> None:
    print(
        'Welcome to the EDPOP explorer!\n'
        'Available commands: {}, next, exit'
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
            records = reader.fetch(arguments[0])
            print('{} records found.'.format(reader.number_of_results))
            show_records(records, shown)
            shown += len(records)
        elif command == 'next':
            if reader is None:
                print('First perform an initial search')
            else:
                records = reader.fetch_next()
                show_records(reader.records, shown)
                shown += len(records)
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
