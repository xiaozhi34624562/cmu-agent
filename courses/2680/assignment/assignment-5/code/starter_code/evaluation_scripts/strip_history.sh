#!/bin/sh
# Leaves an Assignment 4 task's repository with its base commit alone, as `git clone --depth 1` would: HEAD keeps its
# commit id (the task's base_commit), the index, the tracked files and the working tree stay exactly as they were, and
# no older commit is left in .git. prepare_images.sh (step 6) runs it while it builds a task's sandbox image. Without
# it, a task of the same repository at a later base would hold, in its history, the commits that fixed earlier tasks.
#
#   sh strip_history.sh <base_commit> [workdir]     (workdir: /testbed when it is a repository, else /app)
#
# POSIX sh (some task images are Alpine's); exits non-zero, and changes nothing, unless HEAD is base_commit with
# nothing staged.
set -eu
BASE=$1
WD=${2:-}
[ -n "$WD" ] || { WD=/app; [ -d /testbed/.git ] && WD=/testbed; }
export GIT_CONFIG_NOSYSTEM=1
g() { git -C "$WD" -c safe.directory='*' "$@"; }
fail() { echo "strip_history: $WD: $*" >&2; exit 1; }

head=$(g rev-parse HEAD)
[ "$head" = "$BASE" ] || fail "HEAD is $head, not the base commit $BASE"
g diff-index --quiet --cached HEAD -- || fail "the index differs from HEAD"
[ ! -d "$WD/.git/modules" ] || fail "it has initialised submodules (.git/modules), which this script does not carry over"
tree=$(g rev-parse 'HEAD^{tree}')
index=$(g ls-files -s) || fail "git ls-files fails"       # the tracked set, with modes, symlinks and submodule entries
status=$(g status --porcelain) || fail "git status fails"  # untracked files too
branch=$(g symbolic-ref -q --short HEAD || echo main)
owner=$(stat -c %u:%g "$WD/.git")
mode=$(stat -c %a "$WD/.git")

# A new repository that fetches the base commit alone (a shallow fetch), then takes over the old index, so git tracks
# the same files as before (also those that .gitignore matches) and the stat cache stays valid.
T=$(mktemp -d "$WD/../.strip_history.XXXXXX")
git init -q "$T"
git -C "$T" -c safe.directory='*' fetch -q --depth 1 --no-tags --update-head-ok "$WD/.git" "+HEAD:refs/heads/$branch"
git -C "$T" symbolic-ref HEAD "refs/heads/$branch"
cp -p "$WD/.git/index" "$T/.git/index"
for k in core.filemode core.symlinks core.ignorecase core.autocrlf core.eol core.attributesfile core.excludesfile; do
  v=$(git config -f "$WD/.git/config" --get "$k" || true)
  [ -z "$v" ] || git config -f "$T/.git/config" "$k" "$v"
done
[ ! -f "$WD/.git/info/exclude" ] || cp -p "$WD/.git/info/exclude" "$T/.git/info/exclude"
rm -rf "$T/.git/logs" "$T/.git/FETCH_HEAD"
rm -rf "$WD/.git"
mv "$T/.git" "$WD/.git"
rmdir "$T"
chown -R "$owner" "$WD/.git"
chmod "$mode" "$WD/.git"

[ "$(g rev-parse HEAD)" = "$BASE" ] || fail "HEAD changed"
[ "$(g rev-parse 'HEAD^{tree}')" = "$tree" ] || fail "the base tree changed"
[ "$(g rev-list --count --all)" = 1 ] || fail "more than one commit is left"
after=$(g ls-files -s) || fail "git ls-files fails afterwards"
[ "$after" = "$index" ] || fail "the tracked files changed"
after=$(g status --porcelain) || fail "git status fails afterwards"
[ "$after" = "$status" ] || fail "git status changed"
echo "strip_history: $WD keeps only $(echo "$BASE" | cut -c1-12) ($(du -sh "$WD/.git" | cut -f1) of .git)"
