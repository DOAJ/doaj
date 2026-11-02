import multiprocessing

bind = "0.0.0.0:5050"
workers = multiprocessing.cpu_count() * 6 + 1
proc_name = 'doaj'

# Preload the app before forking workers to prevent race conditions
# during index initialization. This ensures initialise_index() runs
# only once instead of once per worker.
preload_app = True

max_requests = 1000

# The maximum jitter to add to the max_requests setting.
#
# The jitter causes the restart per worker to be randomized by
# randint(0, max_requests_jitter)
# This is intended to stagger worker restarts to avoid all workers restarting at the same time.
max_requests_jitter = 100

timeout = 40
graceful_timeout = 40
