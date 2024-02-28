
from functools import wraps
import json
import os
import time
from typing import Any, Callable, cast, Dict, List, TypeVar, Union


Decorator = TypeVar('Decorator', bound=Callable[..., Any])
JSON = Union[List[Any], Dict[str, Any]]


def json_cache_simple(
    path: os.PathLike[str],
    ttl: int = 3600,
) -> Callable[[Decorator], Decorator]:
    """
    Cache function's return value into a single JSON file.

    The wrapped function can't take any arguments as that would invalidate
    the cache, and our simple mtime-based refresh strategy.

    Intended to cache large API requests during development, where the
    return value might be several megabytes of JSON data.

        path = DATA_FOLDER / 'stock-levels.json'

        @json_cache(path, ttl=600)
        def fetch_stock_levels():
            # Slow API request

    Be aware that data undergoing a round-trip through a JSON file will
    lose some type information. Named tuples to plain lists, for example.
    """
    def save_json(path: os.PathLike[str], data: JSON) -> None:
        with open(path, 'wt') as fp:
            json.dump(data, fp)

    def load_json(path: os.PathLike[str]) -> JSON:
        with open(path, 'rt') as fp:
            return json.load(fp)                            # type: ignore[no-any-return]

    def actual(func: Decorator) -> Decorator:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Outlaw non-default arguments
            if args or kwargs:
                raise ValueError("No non-default arguments allowed on wrapped function")

            # Load data from cache file?
            if os.path.exists(path):
                age = time.time() - os.path.getmtime(path)
                if age < ttl:
                    return load_json(path)

            # Run wrapped function, save to cache file.
            data = func()
            save_json(path, data)
            return data

        return cast(Decorator, wrapper)

    return actual
