"""
An extension of the well-worn `syncer.SyncerBase` template class, but assuming
database models as the slave, and model form data from the master - with some
unique key shared between them.

See Eurotech's `locations.spreadsheet` module for an example of synchorising
against an external spreadsheet.
"""


from abc import ABC, abstractmethod
import dataclasses
import logging
from typing import Any, Dict, Iterable, List, Optional, Set, Type, Union

from django import forms
from django.db import models

from animal3.forms.utils import collapse_errors


logger = logging.getLogger(__name__)
Key = Union[int, str]


@dataclasses.dataclass
class SyncerCounts:
    checked: int = 0
    created: int = 0
    updated: int = 0
    deleted: int = 0
    master: int = 0
    slave: int = 0

    def asdict(self) -> Dict[str, int]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ModelData:
    """
    Data from remote source.

    Contains fields of form data, an optional key linking data to a database
    model, and a location string describing where the data was found.
    """
    fields: Dict[str, Any]
    key: Optional[Key]
    location: str


class ModelSynchroniserError(RuntimeError):
    """
    Synchroniser ran into errors, list of same saved to `error_list` attribute.
    """
    def __init__(self, message: str, error_list: Optional[List[str]] = None):
        super().__init__(message)
        if error_list is None:
            error_list = []
        self.error_list = error_list


class ModelSynchroniser(ABC):
    """
    Synchronise models with field data.

    Models will be created, deleted, and updated to match the data from
    the remote master.

    The remote data must include some unique identifier (at least for existing
    models), and all of a model's required fields. Field data is passed through
    a ModelForm instance for confirmation.
    """
    model: Type[models.Model]
    model_form: Optional[Type[forms.ModelForm]]

    def __init__(self, *args, **kwargs):
        """
        Load both master and slave data, using same keys.

        The key can be a model's primary key, or a unique slug, or even some
        compound 'natural key'.
        """
        # Mapping of key to field data
        self.master_data = self.load_data()

        # Mapping of key to existing models
        self.slave_mapping = self.load_models()

        # String of single-line error messages
        self.errors = []

    @abstractmethod
    def get_master_key(self, fields: Dict[str, Any]) -> Optional[Key]:
        """
        Fetch key from field data, if possible.

        Used to find matching model from database records.

        Args:
            fields:
                A single record from `load_data()` method.

        Returns:
            A key to match against models from `load_models()`, or none if
            data is for a new record.
        """
        ...

    def get_slave_key(self, obj: models.Model) -> Key:
        """
        Fetch key from database model.

        Uses model's primary key by default. Override to use another unique
        identifier, eg. a slug or code.
        """
        return obj.pk

    def keys_from_master(self) -> Set[Key]:
        """
        Build set of keys to match against existing models.
        """
        keys = {data.key for data in self.master_data}
        return keys

    def keys_from_slave(self) -> Set[Key]:
        """
        Build set of keys for existing database models.
        """
        keys = set(self.slave_mapping.keys())
        return keys

    @abstractmethod
    def load_data(self) -> Iterable[ModelData]:
        """
        Build list of field data from remote master.
        """

    @abstractmethod
    def load_models(self) -> Dict[Key, models.Model]:
        """
        Build mapping between unique key and an existing database model.
        """

    def update_from_master(self, code: str) -> None:
        fields = self.master_data[code]
        location = fields['spreadsheet_location']
        instance = self.board_types[code]
        form = BoardTypeImporterForm(data=fields, instance=instance)
        self._save_form(form, location)

    def synchronise(self) -> SyncerCounts:
        """
        Run synchronisation from master to slave.

        Returns:
            SyncerCounts dataclass with
        """
        # Fetch keys for comparison
        counts = SyncerCounts()
        master = self.keys_from_master()
        slave = self.keys_from_slave()
        counts.master = len(master)
        counts.slave = len(slave)
        logger.debug(f"{len(master):,} keys from master, {len(slave):,} from database.")

        # Create new database records?
        # Data that doesn't yet have a key, or whose key is not present in database.
        created_keys = self._create_new()
        counts.created = len(created_keys)
        logger.debug(f"Created {counts.created:,} new database records")
        master |= created_keys

        # Delete obsolete models from database
        to_delete = list(slave - master)
        logger.debug(f"Delete {len(to_delete):,} models from database")
        for key in self._sort_keys(to_delete):
            obj = self.slave_mapping[key]
            obj.delete()
            counts.deleted += 1

        # Check existing models for updates
        to_check = list(master & slave)
        logger.debug(f"Check {len(to_check):,} models for updates")
        counts.checked = len(to_check)

        # Update database records
        for data in self.master_data:
            if data.key not in to_check:
                continue

            obj = self.slave_mapping[data.key]
            form = self.model_form(data=data.fields, instance=obj)

            if not form.has_changed():
                continue

            obj = self._save_form(form, data.location)
            if obj is not None:
                counts.updated += 1

        logger.debug(f"Updated {counts.updated:,} database models with new data")

        return counts

    def _create_new(self) -> Set[Key]:
        """
        Create new database records.

        Fields from master data that either doesn't yet have a key, or
        whose key is not present in database.

        Updates to existing records are handled separately.

        Returns:
            Set of newly created keys.
        """
        created_keys = set()
        for data in self.master_data:
            if data.key in self.slave_mapping:
                continue

            form = self.model_form(data=data.fields)
            obj = self._save_form(form, data.location)
            if obj is not None:
                created_keys.add(self.get_slave_key(obj))

        return created_keys

    def _save_form(self, form: forms.ModelForm, location: str) -> Optional[models.Model]:
        """
        Create a single database record via a ModelForm, tracking errors.

        Adds a line to the `errors` attribute if form validation fails.

        Args:
            form:
                Bound form instance
            location:
                String describing source of data, eg. 'row 17'

        Returns:
            A freshly created (or updated) instance.
        """
        if form.errors:
            errors = collapse_errors(form.errors)
            message = f"Error on {location}. {', '.join(errors)}"
            self.errors.append(message)
            logger.debug(message)
            return None

        obj = form.save()
        return obj

    def _sort_keys(self, keys: Set[Key]) -> Iterable[Key]:
        """
        Sort keys for processing.

        You *could* return the input - if you prefer speedy chaos over tidy order.
        """
        return sorted(keys)
