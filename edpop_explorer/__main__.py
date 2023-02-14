from typing import Dict
import readline

from apireader import APIReader
from readers.hpb import HPBReader


readercommands: Dict[str, APIReader] = {
    'hpb': HPBReader
}


def main():
    while True:
        try:
            line = input('# ')
        except EOFError:
            break
        except KeyboardInterrupt:
            print('')
            continue
        if line:
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
            reader = readerclass()
            records = reader.fetch(arguments[0])
            for record in records:
                print(record)
        else:
            print('Command does not exist: {}'.format(command))


if __name__ == '__main__':
    main()
