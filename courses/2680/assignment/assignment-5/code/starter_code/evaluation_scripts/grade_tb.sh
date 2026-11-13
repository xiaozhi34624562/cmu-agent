#!/bin/bash
# Grade ONE Terminal-Bench task in its own container, the way Harbor's verifier does: the task's
# tests/ folder is copied to /tests, stale reward files are removed, and /tests/test.sh runs in the
# task's working directory under bash, as Harbor runs it (bash -c '(/tests/test.sh) > ...'), with its
# output in /logs/verifier/test-stdout.txt. A test.sh whose #! line comes after comments therefore runs
# under bash too, not under the image's sh. In an image of a Debian release past its end of life
# (stretch, buster, bullseye), apt is first pointed at archive.debian.org. The container keeps the
# network it had (the test scripts download their tools). Called by run_all.py after done(k), once
# the agent can no longer reach the container.
#
#   bash evaluation_scripts/grade_tb.sh <container> <tests_dir> <workdir> <timeout_s> <out_dir>
#
# Prints "1" (solved: a reward above 0) or "0" on stdout; exit status 0 either way. The container's
# /logs/verifier is copied to <out_dir>/verifier, and the reward is read there on the host, from
# reward.json or reward.txt, as plain files only (a symlink or anything else is ignored). On
# timeout the reward is 0 and <out_dir>/TIMEOUT is created; run_all.py removes the container after.
set -uo pipefail
C="$1"; TDIR="$2"; WD="$3"; TO="$4"; OUT="$5"
read -r -a DOCKER <<< "${A3_DOCKER:-docker}"   # run_all.py sets it (e.g. "sudo -n -E docker")
rm -rf "$OUT" && mkdir -p "$OUT"

"${DOCKER[@]}" exec -u 0 "$C" sh -c 'rm -rf /tests /logs/verifier && mkdir -p /tests /logs/verifier /logs/agent' \
  > "$OUT/setup.log" 2>&1
"${DOCKER[@]}" cp "$TDIR/." "$C:/tests" >> "$OUT/setup.log" 2>&1
"${DOCKER[@]}" exec -u 0 "$C" chmod +x /tests/test.sh >> "$OUT/setup.log" 2>&1

# Debian 9-11 (stretch, buster, bullseye) are past their end of life, and deb.debian.org no longer has all their
# packages: bullseye's security updates now answer 404. Some test.sh install their tools with apt. In such an image,
# apt is pointed at archive.debian.org before test.sh runs, so test.sh gets its tools as when Terminal-Bench's
# leaderboard was made. Any other image, or one without apt, is left as it is. A second run changes nothing more.
"${DOCKER[@]}" exec -i -u 0 "$C" sh -s >> "$OUT/setup.log" 2>&1 <<'SH' || true
command -v apt-get > /dev/null 2>&1 || exit 0
id=$(sed -n 's/^ID=//p' /etc/os-release 2> /dev/null | tr -d "\"'")
codename=$(sed -n 's/^VERSION_CODENAME=//p' /etc/os-release 2> /dev/null | tr -d "\"'")
case "$id $codename" in "debian stretch" | "debian buster" | "debian bullseye") ;; *) exit 0 ;; esac
for f in /etc/apt/sources.list /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources; do
  [ -f "$f" ] || continue
  sed -i -E -e 's#https?://security\.debian\.org/?([[:space:]]|$)#http://archive.debian.org/debian-security\1#g' \
    -e 's#https?://(deb|security|httpredir|ftp(\.[a-z]+)?)\.debian\.org/#http://archive.debian.org/#g' "$f"
  if [ "$codename" = stretch ]; then   # the archive has no stretch-updates
    sed -i -E '/^[[:space:]]*deb.*archive\.debian\.org.*[[:space:]]stretch-updates([[:space:]]|$)/s/^/# /' "$f"
  fi
done
# The archive's Release files are not refreshed, so their Valid-Until dates may have passed.
echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99archive-debian-org
echo "apt: $codename's sources point at archive.debian.org"
SH

# On timeout: `timeout` TERMs the docker client, -k 5 KILLs it; whatever still runs in the container
# goes when run_all.py removes the container.
rc=0
timeout -k 5 "$TO" "${DOCKER[@]}" exec -w "$WD" "$C" bash -c '(/tests/test.sh) > /logs/verifier/test-stdout.txt 2>&1' \
  > "$OUT/exec.log" 2>&1 || rc=$?
if [[ $rc == 124 || $rc == 137 ]]; then
  echo "TIMEOUT after ${TO}s" > "$OUT/TIMEOUT"
fi
echo "test.sh exit status: $rc" >> "$OUT/exec.log"
"${DOCKER[@]}" cp "$C:/logs/verifier/." "$OUT/verifier" >> "$OUT/setup.log" 2>&1 || true

python3 -I -S - "$OUT" <<'PY'
import json, math, os, stat, sys
out = sys.argv[1]
def plain(name):
    p = os.path.join(out, "verifier", name)
    try:
        st = os.lstat(p)
    except OSError:
        return None
    if not stat.S_ISREG(st.st_mode) or st.st_size > 65536:
        return None
    with open(p) as f:
        return f.read()
reward = 0.0
if not os.path.exists(os.path.join(out, "TIMEOUT")):
    try:
        j = plain("reward.json")
        if j is not None:
            v = json.loads(j)
            if isinstance(v, dict):
                v = v.get("reward", next(iter(v.values()), 0.0))
            reward = float(v)
        else:
            t = plain("reward.txt")
            reward = float(t) if t is not None and t.strip() else 0.0
    except (ValueError, TypeError):
        reward = 0.0
    if not math.isfinite(reward):
        reward = 0.0
open(os.path.join(out, "reward.txt"), "w").write(f"{reward}\n")
print(1 if reward > 0 else 0)
PY
