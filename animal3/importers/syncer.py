"""
Synchronise data from a master copy.
"""

import dataclasses
import logging
from typing import Dict, Set, Union

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


class SyncerBase:
    """
    Template-pattern class to synchronise objects using unique keys.

    Synchronisation is 1-way from a master to a slave. Keys can be integers
    or strings (commonly primary keys or slugs).

    Two full sets of key from master and slave are compared and used to
    produce a list of actions to run in the following order:

        1. Create new items
        2. Delete obsolete items
        3. Update existing items

    Create a subclass and override the core methods below, starting with
    ``keys_from_master()`` and ``keys_from_slave()``.

    Finally call the ``synchronise()`` method and hope for the best.

    Attributes:
        sort_keys (bool):
            Make it easy to follow the action by sorting the keys before
            each operation. Defaults to `True`. Set to `False` if you prefer
            chaos over order.
    """
    sort_keys = True

    def create_from_master(self, key: Key) -> None:
        """
        Create item in slave from master
        """
        raise NotImplementedError("Please implement: create_from_master(self, key)")

    def delete_from_slave(self, key: Key) -> None:
        """
        Delete the item from slave with the given key.
        """
        raise NotImplementedError("Please implement: delete_from_slave(self, key)")

    def keys_from_master(self) -> Set[Key]:
        """
        Fetch all keys from master.

        Should be a set, or at least quack like one. Starting with
        Python 3 a dictionary view will serve, for example.
        """
        raise NotImplementedError("keys_from_master() not implemented")

    def keys_from_slave(self) -> Set[Key]:
        """
        Fetch all keys from slave.

        See `keys_from_master()`
        """
        raise NotImplementedError("keys_from_slave() not implemented")

    def should_update(self, key: Key) -> bool:
        """
        Should the object with the given code be updated?
        """
        return True

    def update_from_master(self, key: Key) -> None:
        """
        Update item in slave from master.

        The item with the given key exists on both the slave and the master,
        but we don't know anything about their contents.
        """
        raise NotImplementedError("Please implement: update_from_master(self, key)")

    def synchronise(self) -> SyncerCounts:
        """
        Run synchronisation from master to slave.

        Returns:
            SyncerCounts dataclass with
        """
        counts = SyncerCounts()

        # 1) Fetch keys for comparison
        master = self.keys_from_master()
        slave = self.keys_from_slave()
        counts.master = len(master)
        counts.slave = len(slave)
        logger.debug("{:,} keys from master, {:,} from slave.".format(
            len(master), len(slave)))

        # 2) Create new items in slave
        to_create = list(master - slave)
        if self.sort_keys:
            to_create.sort()
        logger.debug("Create {:,} items from master".format(len(to_create)))
        for key in to_create:
            self.create_from_master(key)
            counts.created += 1

        # 3) Delete obsolete items from slave
        to_delete = list(slave - master)
        if self.sort_keys:
            to_delete.sort()
        logger.debug("Delete {:,} items from slave".format(len(to_delete)))
        for key in to_delete:
            self.delete_from_slave(key)
            counts.deleted += 1

        # 4) Check common items for update
        to_check = list(master & slave)
        logger.debug("Check {:,} items for updating".format(len(to_check)))
        to_update = [key for key in to_check if self.should_update(key)]
        counts.checked = len(to_check)

        # 5) Update existing items
        logger.debug("Update {:,} items from master".format(len(to_update)))
        if self.sort_keys:
            to_update.sort()
        for item in to_update:
            self.update_from_master(item)
            counts.updated += 1

        return counts
