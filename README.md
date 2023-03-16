# edpop-explorer
Commandline tool to explore the APIs to be included in the EDPOP VRE

## Install

To install locally, type (inside or outside a virtual environment):

    # pip install .

The tool can then be run using the `edpopx` command.

For development purposes it may be better to use the `--editable` option:

    # pip install --editable .

This way, the source code will be read directly from the original directory
when running the application and changes will have immediate effect.

## Usage

Start the programme from the command line using the `edpopx` command:

    $ edpopx

To perform a search on a database, give the name of the database followed by
the query you want to perform, such as:

    # hpb gruninger

This will give you the number of results and a summary of the first ten
results. To load more results, use the `next` command:

    # next

The results are numbered. Use the `show` command to see the contents of a
particular record:

    # show 8

To exit, type Ctrl+D or use the `exit` command:

    # exit

## Design

The commandline programme in `__main__.py` uses the common interface of
the `APIReader` and `APIRecord` classes to query the various databases that
EDPOP is ought to support. Interfaces to concrete APIs, such as Gallica and
HPB, are defined using classes that inherit from these two classes.

Class hierarcy (interfaces to concrete APIs in bold):

- APIReader / APIRecord
  - SRUReader
    - **GallicaReader** / GallicaRecord
    - **CERLThesaurusReader** / CERLThesaurusRecord
    - SRUMarc21Reader / Marc21Record
      - **HPBReader**
      - **VD16Reader**
      - **VD17Reader**
      - **VD18Reader**
  - SparqlReader / SparqlRecord
    - **STCNReader**
