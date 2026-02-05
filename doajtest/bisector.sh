#!/usr/bin/env bash
# language: bash
# Save as tools/find_culprit.sh and make executable (chmod +x ...)

#set -euo pipefail
#
#TMPDIR=$(mktemp -d)
#ALL="$TMPDIR/all_tests.txt"
#OTHERS="$TMPDIR/others.txt"
#LOCKS="$TMPDIR/locks.txt"
#
#pytest --collect-only -q > "$ALL"
#
#grep 'test_lock.py' "$ALL" > "$LOCKS" || true
#grep -v 'test_lock.py' "$ALL" > "$OTHERS" || true
#
#if [ ! -s "$LOCKS" ]; then
#  echo "No tests found in test_lock.py"
#  rm -rf "$TMPDIR"
#  exit 1
#fi
#
#mapfile -t LOCK_ARR < "$LOCKS"
#mapfile -t OTHER_ARR < "$OTHERS"
#N=${#OTHER_ARR[@]}
#
#if [ "$N" -eq 0 ]; then
#  echo "No other tests to blame; run `pytest ${LOCK_ARR[*]}` manually."
#  rm -rf "$TMPDIR"
#  exit 0
#fi
#
#run_with_lock() {
#  # $1..$k are nodeids from OTHER_ARR, then append LOCK_ARR
#  local nodes=("$@")
#  nodes+=("${LOCK_ARR[@]}")
#  pytest -q "${nodes[@]}" >/dev/null 2>&1
#  return $?
#}
#
#low=0
#high=$N
#
#while [ $((high - low)) -gt 1 ]; do
#  mid=$(((low + high) / 2))
#  subset=("${OTHER_ARR[@]:0:mid}")
#  echo "Testing first $mid of $N tests..."
#  if run_with_lock "${subset[@]}"; then
#    echo "PASS -> culprit is in tests [$mid..$((N-1))]"
#    low=$mid
#  else
#    echo "FAIL -> culprit is in first $mid tests"
#    high=$mid
#  fi
#done
#
## Report suspects: small slice around boundary
#start=$((low - 2)); [ $start -lt 0 ] && start=0
#end=$((low + 3)); [ $end -gt $N ] && end=$N
#
#echo
#echo "Suspect tests (run these before test_lock.py to reproduce):"
#for i in $(seq $start $((end - 1))); do
#  printf '  %s\n' "${OTHER_ARR[$i]}"
#done
#
#echo
#echo "Re-run one of the suspect sets manually, e.g.:"
#echo "  pytest -q ${OTHER_ARR[$start]} ${LOCK_ARR[*]}"
#rm -rf "$TMPDIR"


set -euo pipefail

TMPDIR=$(mktemp -d)
ALL="$TMPDIR/all_tests.txt"
OTHERS="$TMPDIR/others.txt"
LOCKS="$TMPDIR/locks.txt"

# timeout in seconds for running test_lock.py (adjust as needed)
TIMEOUT_SECONDS=65

pytest --collect-only -q > "$ALL"

grep 'test_lock.py' "$ALL" > "$LOCKS" || true
grep -v 'test_lock.py' "$ALL" > "$OTHERS" || true

if [ ! -s "$LOCKS" ]; then
  echo "No tests found in test_lock.py"
  rm -rf "$TMPDIR"
  exit 1
fi

mapfile -t LOCK_ARR < "$LOCKS"
mapfile -t OTHER_ARR < "$OTHERS"
N=${#OTHER_ARR[@]}

if [ "$N" -eq 0 ]; then
  echo "No other tests to blame; run \`pytest ${LOCK_ARR[*]}\` manually."
  rm -rf "$TMPDIR"
  exit 0
fi

run_with_lock() {
  # Temporarily disable -e so failures/timeouts don't exit the whole script
  set +e
  local nodes=("$@")
  nodes+=("${LOCK_ARR[@]}")

  if command -v timeout >/dev/null 2>&1; then
    # Use GNU timeout; --preserve-status keeps pytest exit codes, --foreground helps pytest handle signals
    timeout --preserve-status --foreground "${TIMEOUT_SECONDS}s" pytest -q "${nodes[@]}" >/dev/null 2>&1
    rc=$?
    # timeout returns 124 on timeout, 137 if killed; treat these as failure (non-zero)
    if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
      echo "pytest timed out after ${TIMEOUT_SECONDS}s"
      rc=1
    fi
    set -e
    return $rc
  else
    # Portable fallback: run pytest in background and kill it if it exceeds TIMEOUT_SECONDS
    pytest -q "${nodes[@]}" >/dev/null 2>&1 &
    pid=$!
    end_time=$((SECONDS + TIMEOUT_SECONDS))
    rc=0
    while kill -0 "$pid" >/dev/null 2>&1; do
      if [ "$SECONDS" -ge "$end_time" ]; then
        echo "pytest timed out after ${TIMEOUT_SECONDS}s; terminating (pid $pid)"
        kill -TERM "$pid" 2>/dev/null || true
        sleep 5
        kill -KILL "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
        rc=1
        break
      fi
      sleep 1
    done
    # If process exited normally before timeout, capture its exit code
    if kill -0 "$pid" >/dev/null 2>&1; then
      # already handled timeout and killed
      :
    else
      wait "$pid" >/dev/null 2>&1 || rc=$?
      # if pytest returned non-zero, rc will reflect that
    fi
    set -e
    return $rc
  fi
}

low=0
high=$N

while [ $((high - low)) -gt 1 ]; do
  mid=$(((low + high) / 2))
  subset=("${OTHER_ARR[@]:0:mid}")
  echo "Testing first $mid of $N tests..."
  if run_with_lock "${subset[@]}"; then
    echo "PASS -> culprit is in tests [$mid..$((N-1))]"
    low=$mid
  else
    echo "FAIL -> culprit is in first $mid tests"
    high=$mid
  fi
done

# Report suspects: small slice around boundary
start=$((low - 2)); [ $start -lt 0 ] && start=0
end=$((low + 3)); [ $end -gt $N ] && end=$N

echo
echo "Suspect tests (run these before test_lock.py to reproduce):"
for i in $(seq $start $((end - 1))); do
  printf '  %s\n' "${OTHER_ARR[$i]}"
done

echo
echo "Re-run one of the suspect sets manually, e.g.:"
echo "  pytest -q ${OTHER_ARR[$start]} ${LOCK_ARR[*]}"
rm -rf "$TMPDIR"
