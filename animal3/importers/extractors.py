
from abc import ABC, abstractmethod
import collections
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


class Extractor(ABC):
    """
    Read field data from some input.

    Data is always extracted as a dictionary of field values that can be
    passed on to a model form for further processing and validation.
    """

    @abstractmethod
    def fields(self, model_tag: str) -> Iterable[Dict[str, Any]]:
        """
        Iterate over dictionaries of field data using a generator.

        Args:
            model_tag:
                Identify which model the client needs, eg. 'contact.message'

        Returns:
            A generator over field data.
        """


class DumpdataJSON(Extractor):
    """
    Produce field data from the JSON file produced by Django's dumpdata command.
    """

    def __init__(self, path: Path):
        """
        Read Django dumpdata export using JSON format.

        Args:
            path:
                Path to JSON file.
        """
        self.path = path
        self.data = self._load(path)

    def fields(self, model_tag: str) -> Iterable[Dict[str, Any]]:
        try:
            yield from self.data[model_tag]
        except KeyError:
            raise KeyError(f"No fields found with model_tag {model_tag!r}") from None

    def _load(self, path: Path) -> Dict[str, Any]:
        """
        Read model data from a Django JSON dumpdata export.

        The input data is a list of dicts, each with three keys: the
        name of the model, its primary key from the database, and another
        dictionary containing its fields.

        For example:
            [
                {
                    "model": "contact.message",
                    "pk": 1,
                    "fields": {...}
                },
                {
                    "model": "contact.recipient",
                    "pk": 1,
                    "fields": {...},
                }
            ]

        Args:
            path:
                Path to JSON file.

        Raises:
            ValueError:
                If the input data fails validation. You can view the problem
                record using the command-line ``jq`` command, for example:

                    $ jq '.[-1]' ../export/contact.json

        Returns:
            The same field data, but rearranged for efficient processing:

            {
                'contact.message': [{...}, ...],
                'contact.recipient': [{...}, ...]
            }

            There is now a for each model name and the pk and the field data
            are wrapped in a 2-tuple.
        """
        # Read data
        data = collections.defaultdict(list)
        with open(path, 'rt') as fp:
            for index, record in enumerate(json.load(fp)):
                try:
                    model_tag, cleaned = self._clean(index, record)
                finally:
                    pass

                data[model_tag].append(cleaned)
        return dict(data)

    def _clean(
        self,
        index: int,
        record: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Helper method for `read_data()` to process a single JSON record.

        Args:
            index:
                The 0-index of the JSON record.

        Raises:
            ValueError:
                If record doesn't match expected format.

        Returns:
            A 2-tuple of the model tag, and the field data.
        """
        # Check format
        expected_keys = {'model', 'pk', 'fields'}
        if record.keys() != expected_keys:
            message = (
                f"Error with JSON record {index}: Expected mapping with keys "
                f"{sorted(expected_keys)}, but found {sorted(record)}"
            )
            raise ValueError(message)

        # Place pk in first position
        fields = {'pk': record['pk']}
        fields.update(record['fields'])
        model_tag = record['model']
        return (model_tag, fields)
