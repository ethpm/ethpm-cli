import collections
from typing import Any, Iterable, List

from eth_utils import to_list


@to_list
def flatten(item: List[Any]) -> Iterable[Any]:
    for el in item:
        if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el
