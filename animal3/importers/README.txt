
Flowchart
=========

This is a lightweight Extract, Transform, Load (ETL) system. We extract fields from
a JSON file, filter by model, transform them to match the current model, then load
the data using a Django ModelForm to handle verification and type transformation.

 Extract -> Transform -> Load


## Extract

Produces data dictionaries from source.

These are plain Python dictionaries with string keys and various value types.
The types (and possibly key names) will be adapted by the next step. Files are
relative paths into a media folder.

There is usually one type of extractor per data source and one extractor subclass
per model. For example, a dumpdata import command uses `DumpdataJSON` extractors
to pull data out of a Django dumpdata file, with one subclass defined to
filter out the records relevant to each database model.


## Transform

Modify a dictionary of data from the extractor class to better fit our database
model.

A plain Python dictionary goes in, and a plain dictionary comes out. Keys may
be renamed or removed, and values be converted or even invented. Files are loaded
from the media folder. The output dictionary should be valid data for the loader
class' model form.

There are typically several transformer classes per model, one for each generation
or variation of incoming data. The first one not to error out on the first extracted
record will be picked by the loader.


## Loader

Loads the data from the chosen transformer class into the database via a model
form.


##

 #. The ``ImportCommmand`` class manages the whole thing.
 #. It creates a ``DumpdataJSONExtractor`` class to read raw dictionaries from
    the input file. The extractor also provides facilities to filter its data by model.
 #. The command class contains a sequence of ``Loader`` clases. These are run in
    order so that dependencies between model types can be satisfied.
 #. The loader classes are responsible for running transformers against the raw
    data and for validating it using model forms.
