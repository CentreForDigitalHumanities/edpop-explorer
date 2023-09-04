Introduction
============

.. note::

   This chapter is not yet complete.

About
-----

There are many library catalogues and heritage databases nowadays that
have a public API or a downloadable dataset, which makes it possible to
use their data in other applications. However, despite the great
and longstanding efforts to harmonize library data with standards
such as Marc21, BIBFRAME and authority files such as FAST, there is
still too much variety in standards to combine data from different
APIs and downloadable datasets right away. ``edpop-explorer``
aims to provide a common interface to multiple catalogues to
both querying and results, while keeping the original data
available at all times.

``edpop-explorer`` was created as part of the EDPOP project, [#]_ an 
international network that stimulates innovative research on European 
popular print culture. In this project, a virtual research environment
(VRE) is being created to gather and annotate metadata of items in popular
print culture. The VRE will rely on ``edpop-explorer``.

.. [#] https://edpop.wp.hum.uu.nl/

Getting started
---------------

Python API
^^^^^^^^^^

A basic search in the Heritage of the Printed Book database of CERL
(HPB) looks like this: ::

    >>> from edpop_explorer.readers import HPBReader
    >>> reader = HPBReader()
    >>> reader.set_query("gruninger")
    >>> reader.fetch()  # Start fetching, fetch 10 at a time
    >>> reader.number_of_results  # Total number of results for query
    2134
    >>> reader.number_fetched  # Number of results that have been fetched so far
    10
    >>> record = reader.records[0]  # A Record object
    >>> title = record.title  # A Field object 
    >>> print(title)
    The book of the Mainyo-i-khard
    >>> graph = record.to_graph()  # Get an rdflib graph for this record
    >>> print(graph.serialize())  # Get turtle serialization
    [] a edpoprec:BibliographicalRecord ;
        edpoprec:dating [ a edpoprec:Field ;
                edpoprec:originalText "1871" ] ;
        edpoprec:fromCatalog <https://dhstatic.hum.uu.nl/edpop-explorer/catalogs/hpb> ;
        edpoprec:identifier "UkWE.01.B25967" ;
        edpoprec:publicURL "http://hpb.cerl.org/record/UkWE.01.B25967" ;
        edpoprec:publisherOrPrinter [ a edpoprec:Field ;
                edpoprec:originalText "Carl Grüninger, Augustenstrasse 7 ; Messrs. Trübner and Co., 60 Paternoster Row" ] ;
        edpoprec:title [ a edpoprec:Field ;
                edpoprec:originalText "The book of the Mainyo-i-khard" ] .

Commandline tool
^^^^^^^^^^^^^^^^

Start the programme from the command line using the ``edpopx`` command: ::

    $ edpopx

To perform a search on a database, give the name of the database followed by
the query you want to perform, such as: ::

    $ hpb gruninger

This will give you the number of results and a summary of the first ten
results. To load more results, use the ``next`` command: ::

    $ next

The results are numbered. Use the ``show`` command to see the contents of a
particular record (use ``showrdf`` to see RDF and ``showraw`` to see the original
record data converted to YAML): [#]_ ::

    $ show 8

To exit, type Ctrl+D or use the ``quit`` command: ::

    $ quit

.. [#] Internally, this data is stored as a Python ``dict`` or as a Python 
   object that can be serialized as a Python ``dict``. The conversion to
   YAML is done to produce output in a form that is easily readable.
