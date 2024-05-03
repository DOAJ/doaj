import time
from typing import Callable


def wait_until(cond_fn: Callable[[], bool], timeout=10, sleep_time=0.1,
               timeout_msg='fail to meet the condition within the timeout period.'):
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        cond_result = cond_fn()
        if cond_result:
            return cond_result

        time.sleep(sleep_time)

    raise TimeoutError(timeout_msg)
