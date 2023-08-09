[![PyPI Version](https://img.shields.io/pypi/v/edpop-explorer)](https://pypi.org/project/edpop-explorer/)

# edpop-explorer
EDPOP Explorer is a Python library and commandline application that offers a common 
interface to multiple library catalogues and bibliographical databases, such as the 
Heritage of the Printed Book Database (HPB), the Universal Short Title Catalogue 
(USTC), and the Bibliothèque nationale de France (BnF). It aims to normalize the 
most important information from the metadata while keeping all original metadata 
available. The data can be accessed as RDF data or directly from Python objects.

## Install

`edpop-explorer` can easily be installed from PyPI:

    # pip install edpop-explorer

The tool can then be run using the `edpopx` command. (On Windows it may
be that the `edpopx` command does not become available on the path. In that
case you can also run it using the command `python -m edpop_explorer`.)

For development purposes, clone the repository and use the ``--editable``
option:

    # pip install --editable .

This way, the source code will be read directly from the original directory
when running the application and changes will have immediate effect.

## Usage

(This section documents the commandline tool.)

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

To exit, type Ctrl+D or use the `quit` command:

    # quit

## Design

The commandline programme in `__main__.py` uses the common interface of
the `APIReader` and `APIRecord` classes to query the various databases that
EDPOP is ought to support. Interfaces to concrete APIs, such as Gallica and
HPB, are defined using classes that inherit from these two classes.

Class hierarcy (interfaces to concrete APIs are in bold -- these are located
in the `readers` subpackage):

- APIReader / APIRecord
  - SRUReader
    - **GallicaReader** / GallicaRecord
    - **CERLThesaurusReader** / CERLThesaurusRecord
    - **BibliopolisReader** / BibliopolisRecord
    - **KBReader** / KBRecord
    - SRUMarc21Reader / Marc21Record
      - **HPBReader**
      - **VD16Reader**
      - **VD17Reader**
      - **VD18Reader**
      - **BnFReader**
  - SparqlReader / SparqlRecord
    - **STCNReader**
  - **SBTIReader** / SBTIRecord
  - **FBTEEReader** / FBTEERecord
  - **USTCReader** / USTCRecord
