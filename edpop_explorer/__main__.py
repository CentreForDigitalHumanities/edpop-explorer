import readline
from appdirs import AppDirs
from pathlib import Path

from edpop_explorer.edpopxshell import EDPOPXShell


try:
    from colorama import just_fix_windows_console
    just_fix_windows_console()
except ImportError:
    pass

historyfile = Path(AppDirs('edpop-explorer', 'cdh').user_data_dir) / 'history'


def save_history() -> None:
    if not historyfile.parent.exists():
        historyfile.parent.mkdir(parents=True)
    readline.write_history_file(historyfile)


def main() -> None:
    if historyfile.exists():
        readline.read_history_file(historyfile)
    EDPOPXShell().cmdloop()
    save_history()


if __name__ == '__main__':
    main()
