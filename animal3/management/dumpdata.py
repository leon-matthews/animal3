
import collections
import logging
from pathlib import Path
import shutil
import time
from typing import Any, Iterable, List, Optional, Type, Union

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from animal3.importers import DumpdataJSON, Extractor, Loader
from animal3.utils.files import count_files

from .base import (
    CommandBase, CommandParser, ConfirmationMixin, existing_file_type, existing_folder_type,
)


logger = logging.getLogger(__name__)
PathType = Union[Path, str]


class ImportCommmand(ConfirmationMixin, CommandBase):
    """
    Replace all application data with a dumpdata file and a media folder.

    Attributes:
        loaders:
            A tuple or list of Loader classes that will be instantiated
            and run in the order in which they're given. Values of None
            are skipped to allow for configuration.

    """
    loaders: Iterable[Optional[Type[Loader]]]

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Run importer.

        Options:
            dumpdata:
                Path to source of old data.
            media:
                Path to root of old media.
        """
        dumpdata = options['dumpdata']
        extractor = self.build_extractor(dumpdata)
        media_root = options['media']
        loaders = self.build_loaders(extractor, media_root)
        app_label = self.find_app_label(loaders)
        if app_label:
            self.delete_media(app_label)
        self.run_loaders(loaders)

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Prompt user for paths to JSON data and media to import.
        """
        super().add_arguments(parser)
        parser.add_argument(
            '-d',
            '--dumpdata',
            metavar='DUMPDATA',
            required=True,
            type=existing_file_type,
            help="Path to JSON file from dumpdata command",
        )
        parser.add_argument(
            '-m',
            '--media',
            metavar='MEDIA_ROOT',
            type=existing_folder_type,
            help="Optional path to media folder to import",
        )

    def build_extractor(self, path: Path) -> DumpdataJSON:
        """
        Read source of model data from an extractor instance.

        Args:
            path:
                Path to JSON dumpdata file

        Returns:
            An extractor instance.
        """
        # Create extractor
        start = time.perf_counter()
        extractor = DumpdataJSON(path)
        elapsed = time.perf_counter() - start

        # Print report
        file_size = path.stat().st_size
        logger.info(f"Read {file_size:,} bytes of JSON data (in {elapsed:.3f}s):")
        for key in extractor.data:
            logger.info(f"    {key!r}: {len(extractor.data[key]):,} records")
        return extractor

    def build_loaders(self, extractor: Extractor, media_root: Path) -> List[Loader]:
        """
        Instantiate our list of loader types in our class attribute.

        Args:
            extractor:
                Our source of incoming field data.

        Returns:
            List of loader instances.
        """
        loaders = []
        for loader_class in self.loaders:
            if loader_class is None:
                continue

            if not issubclass(loader_class, Loader):
                raise ImproperlyConfigured(
                    f'{loader_class.__name__} is not a Loader class'
                )

            loader = loader_class(extractor, media_root)
            loaders.append(loader)
        return loaders

    def delete_media(self, app_label: str) -> None:
        """
        Delete app's media folder, if it exists.

        Args:
            app_label:
                Relative path to current app. media under MEDIA_ROOT, eg. 'news'.

        Returns:
            None
        """
        # Anything to delete?
        media_folder = Path(settings.MEDIA_ROOT) / app_label
        if not media_folder.exists():
            logger.info("Destination media folder does not exist: %s", media_folder)
            return

        num_files = count_files(media_folder)
        self.warning(
            f"Deleting {num_files} existing files from MEDIA_ROOT/{app_label}/"
        )
        shutil.rmtree(media_folder)

    def find_app_label(self, loaders: Iterable[Loader]) -> Optional[str]:
        """
        Find the app label for the loader's models, ie. the new models.

        Raises:
            ImproperlyConfigured:
                If models don't all have the same label.

        Returns:
            The label for the app that the new models belong to, eg. 'contact'.
            None if no models found.
        """
        label = last = None
        for loader in loaders:
            label = loader.model._meta.app_label
            if (last is not None) and (label != last):      # type: ignore[unreachable]
                raise ImproperlyConfigured(
                    f"Models from different apps found: {label!r} and {last!r}"
                )
            last = label
        return label

    def run_loaders(self, loaders: Iterable[Loader]) -> None:
        """
        Instantiate and run loader classes in the `self.loaders`, in order.

        Args:
            loaders:
                Loader instances to run.

        Returns:
            None
        """
        # Delete existing models
        num_deleted: collections.Counter[str] = collections.Counter()
        for loader in loaders:
            counts = loader.delete_existing()
            num_deleted.update(counts)

        # Python 3.10: Replace with ``num_deleted.total()``
        num_deleted_total = sum(num_deleted[k] for k in num_deleted)
        if num_deleted:
            self.warning(
                f"Deleted {num_deleted_total:,} existing models in total"
            )
            for label, count in num_deleted.most_common():
                logger.info(f"Deleted {count:,} {label} models")

        # Create new models
        for loader in loaders:
            start = time.perf_counter()
            num_created, num_skipped = loader.run()
            elapsed = time.perf_counter() - start
            self.success(
                f"Created {num_created:,} new {loader.get_model_name()} models "
                f"in {elapsed:.1f} seconds. Skipped {num_skipped:,}."
            )
