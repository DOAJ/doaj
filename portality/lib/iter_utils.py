from itertools import islice
from typing import Iterable, Any


def batched(iterable: Any, n: int) -> Iterable[Iterable[Any]]:
    """
    Batch data into tuples of length n. The last batch may be shorter.
    batched('ABCDEFG', 3) --> ABC DEF G
    copy from more-itertools
    """
    #
    if n < 1:
        raise ValueError('n must be at least one')

    it = iter(iterable)
    while True:
        batch = tuple(islice(it, n))
        if not batch:
            break
        yield batch
