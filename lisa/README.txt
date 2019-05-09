This folder contains the LISA document collection, and has three files, as follows:

1. lisa.all.txt
---------------

Contains all documents in the LISA collection (6004 in total).

Each document begins with a document identifer, then a document
title, and finally the document itself after an empty line.

The end of each document is marked with a line of asterisk 
characters.

2. lisa.queries.txt
-------------------

Contains sample queries for the LISA collection (35 in total).

Each query begins with a query identifier on a line by itself.

The query text follows on the next line, and is ended with a
hash (#) symbol.

3. lisa.relevance.txt
---------------------

Contains relevance judgments for the 35 queries in the 
lisa.queries.txt file.

The entry for each query has 3 parts:
   1. The query identifier.
   2. The number of judged relevant documents.
   3. A list of the document identifiers of the judged
      relevant documents.

Any documents not contained in this file are considered to be
non-relevant.