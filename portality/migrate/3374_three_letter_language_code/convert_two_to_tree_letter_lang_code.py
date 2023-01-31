import time

from portality import models
from portality.lib import iter_utils


def main(batch_size=1000):
    start_time = time.time()

    def _cur_time():
        return f'{time.time() - start_time:,.2f}s'

    for target_type in [
        # models.Journal,
        # models.Application,
        models.Article,
    ]:
        records_list = iter_utils.batched(target_type.iterall(), batch_size)
        for i, sub_list in enumerate(records_list):
            msg = f'update records [{target_type.__name__}][{i * batch_size:,.0f}][{_cur_time()}]'
            print(f'{msg:<100}', end='\r')

            # isolang from __SEAMLESS_COERCE__ will auto convert 2-letter to 3-letter lang code
            target_type.bulk((i.data for i in sub_list))
        print(f'[{target_type.__name__}] updated')

    print(f'total time: {_cur_time()}')


if __name__ == '__main__':
    main()
