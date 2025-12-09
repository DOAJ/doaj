# python
import os
import sys
import threading
import subprocess
import faulthandler
import time

# Name fragment of the test that fails when run in the full suite
_TARGET = "test_lock.py"

def _dump_state(label):
    pid = os.getpid()
    print(f"\n=== STATE DUMP: {label} (pid={pid}) ===", file=sys.stderr)
    # Python threads
    print("Threads:", file=sys.stderr)
    for t in threading.enumerate():
        print(f"  {t.name!s} alive={t.is_alive()} daemon={t.daemon}", file=sys.stderr)

    # Python-level stacks
    print("\nPython thread stacks (faulthandler):", file=sys.stderr)
    faulthandler.dump_traceback(file=sys.stderr, all_threads=True)

    # child processes whose parent is this pid (may be empty if detached)
    print("\nChild processes (ps --ppid):", file=sys.stderr)
    try:
        subprocess.run(["ps", "-o", "pid,ppid,cmd", "--ppid", str(pid)],
                       check=False, text=True, stdout=sys.stderr)
    except Exception as e:
        print("  failed to run ps:", e, file=sys.stderr)

    # open file descriptors for this process (Linux /proc)
    try:
        fds = os.listdir(f"/proc/{pid}/fd")
        print(f"\nOpen fds: {len(fds)}", file=sys.stderr)
        # print a small sample
        for fd in sorted(fds)[:50]:
            try:
                target = os.readlink(f"/proc/{pid}/fd/{fd}")
            except Exception:
                target = "<unreadable>"
            print(f"  fd {fd}: {target}", file=sys.stderr)
    except Exception as e:
        print("  cannot list /proc fds:", e, file=sys.stderr)

    # optional: lsof for full listing if available (may be noisy)
    try:
        subprocess.run(["lsof", "-p", str(pid)], check=False, text=True, stdout=sys.stderr, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    print("=== END STATE DUMP ===\n", file=sys.stderr)


def pytest_runtest_setup(item):
    # keep output small: only emit detailed dumps for the target test or every 50th test
    if _TARGET in item.nodeid:
        _dump_state(f"before {item.nodeid}")


def pytest_runtest_teardown(item, nextitem):
    if _TARGET in item.nodeid:
        # short pause so any background cleanup can run, then snapshot state
        time.sleep(0.1)
        _dump_state(f"after {item.nodeid}")


def pytest_sessionfinish(session, exitstatus):
    # keep your existing final dump too (helps when the process hangs after sessionfinish)
    print("\n=== pytest_sessionfinish: active threads ===", file=sys.stderr)
    for t in threading.enumerate():
        print(f"  {t.name!s} alive={t.is_alive()} daemon={t.daemon}", file=sys.stderr)

    print("\n=== Python thread stacks (faulthandler) ===", file=sys.stderr)
    faulthandler.dump_traceback(file=sys.stderr, all_threads=True)

    print("\n=== child processes (ps) ===", file=sys.stderr)
    try:
        subprocess.run(["ps", "-o", "pid,ppid,cmd", "--ppid", str(os.getpid())],
                       check=False, text=True, stdout=sys.stderr)
    except Exception as e:
        print("  failed to list children:", e, file=sys.stderr)