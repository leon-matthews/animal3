
import logging


logger = logging.getLogger(__name__)


def find_cached_node(model, tree):                              # type: ignore
    """
    Find the node in the cached tree matching the given model's primary key.

    This is useful if you want to run tree methods on a MPTT model and already
    have an MPTT cached tree available. Running the tree methods on the node
    in the cached tree will not incur any database queries.
    """
    # Recursively examine nodes
    def search(model, node):                                    # type: ignore
        if model.pk == node.pk:
            return node

        for node in node.get_children():
            found = search(model, node)
            if found:
                return found

    # Search top-level nodes
    for node in tree:
        found = search(model, node)
        if found:
            return found

    logger.warning("Could not find '%r' with pk=%s in cached tree", model, model.pk)
    return None


def find_ancestors(current):                                    # type: ignore
    """
    Return list of the current nodes ancestors.

    Needed because (as of MPTT 0.8.6) simply calling `get_ancestors()` on a
    root node triggers a DB query, even in a cached tree.
    """
    if not current:
        return []
    elif current.is_root_node():
        return [current]
    else:
        return current.get_ancestors(include_self=True)
