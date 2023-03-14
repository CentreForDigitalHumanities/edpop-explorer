# edpop-explorer
Commandline tool to explore the APIs to be included in the EDPOP VRE

## Install

To install locally, type (inside or outside a virtual environment):

    # pip install .

`edpop-explorer` can then be run using `python -m edpop_explorer`.

For development purposes it may be better to use the `--editable` option:

    # pip install --editable .

This way, the source code will be read directly from the original directory
when running the application and changes will have immediate effect.

## Usage

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

This tool is built up as an executable Python package called
`edpop_explorer`
