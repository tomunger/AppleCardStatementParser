# Apple Card Statement Parser

The Apple Card has great privacy features, which I like, but limited data export, which
is an inconvenience.  So far, I can only export monthly statements as a PDF file.

This tool will parse an apple statement PDF to a single CSV file which can then be imported 
to a spreadsheet program.  

I add columns for category and a "shared" flag.  

This parser worked on the September statement.  I don't think Apple will change statement format
that often, but the card is a new product so this parser must be considered in Alpha stage.

## Requirements

`requirements-to-freeze` is the list of top level modules needed.

`requirements.txt` is the list of modules that got installed.

camelot also requires `ghostscript` to be installed on your system

On Macs, you can use brew:  `brew install tcl-tk ghostscript`

But I did my development on Ubuntu.

## Camelot PDF parser

More documentation is on [readthedocs](https://camelot-py.readthedocs.io/en/master/)

## Running

. env/bin/activate
python3 applecardstatement.py PDF-File CSV-File

    python3 applecardstatement.py ../../../Documents/finance/statements/applecard/apple\ card\ 2019-11.pdf ../../../Documents/finance/statements/applecard/apple\ card\ 2019-11.csv

