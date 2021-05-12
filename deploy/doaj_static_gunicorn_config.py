bind = "0.0.0.0:5051"
workers = 2
proc_name = 'doaj (static)'
max_requests = 1000

# The maximum jitter to add to the max_requests setting.
#
# The jitter causes the restart per worker to be randomized by
# randint(0, max_requests_jitter)
# This is intended to stagger worker restarts to avoid all workers restarting at the same time.
max_requests_jitter = 100

timeout = 40
graceful_timeout = 40
