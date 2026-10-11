#!/usr/bin/env bash

# Unit test intended to both demonstrate supported xxhsum fallback use cases
#   and to ensure xxhsum fallback is accurate

tl=$(git rev-parse --show-toplevel)
sources=(${tl}/dev/tests/test-funcs)
sources+=(${tl}/static/client/functions/{math,logging,utility})
sources+=(${tl}/static/client/sources/xxhsum/xxhsum)
for s in ${sources[@]}; do source $s; done

command xxhsum <<<"test" &>/dev/null || {
  __gs_errormsg "\`xxhsum\` is not installed"
  exit 1
}

echo "Unit test for static/client/sources/xxhsum started"

run_xxhsum_tests() {
  local total=0 pass=0 fail=0 file

  printf '\n--- default (64) ---\n'
  for file in "${sources[@]}"; do
    _assert -e USE_GS_XXHSUM=y xxhsum "$(xxhsum "$file")" "$file"
  done

  printf '\n--- -H0 (32) ---\n'
  for file in "${sources[@]}"; do
    _assert -e USE_GS_XXHSUM=y xxhsum "$(xxhsum -H0 "$file")" -H0 "$file"
  done

  printf '\n--- -H1 (64) ---\n'
  for file in "${sources[@]}"; do
    _assert -e USE_GS_XXHSUM=y xxhsum "$(xxhsum -H1 "$file")" -H1 "$file"
  done


  local TIMEFORMAT='%5R'
  local custom real size

  printf '\n--- time difference (64) ---\n'
  for file in "${sources[@]}"; do
    custom=$( (time USE_GS_XXHSUM=y xxhsum "$file" &>/dev/null) 2>&1 )
    real=$( (time xxhsum -H1 "$file" &>/dev/null) 2>&1 )
    read -r size _ < <(du -sh "$file")
    echo "  difference -> $custom (bash version) - $real (native) = $(__gs_calc "$custom-$real") ($(__gs_calc -d 2 "$custom/$real")x slower) (file size $size)"
  done

  printf '\n--- time difference (32) ---\n'
  for file in "${sources[@]}"; do
    custom=$( (time USE_GS_XXHSUM=y xxhsum -H0 "$file" &>/dev/null) 2>&1 )
    real=$( (time xxhsum -H1 "$file" &>/dev/null) 2>&1 )
    read -r size _ < <(du -sh "$file")
    echo "  difference -> $custom (bash version) - $real (native) = $(__gs_calc "$custom-$real") ($(__gs_calc -d 2 "$custom/$real")x slower) (file size $size)"
  done

  printf '\n--- errors ---\n'
  ASSERT_IGNORE_RET=y _assert -e USE_GS_XXHSUM=y xxhsum "$(xxhsum 2>&1)"
  ASSERT_IGNORE_RET=y _assert -e USE_GS_XXHSUM=y xxhsum "$(xxhsum /gs-trash 2>&1)" /gs-trash
  _assert_fail -e USE_GS_XXHSUM=y xxhsum
  _assert_fail -e USE_GS_XXHSUM=y xxhsum /gs-trash

  printf '\nSummary: pass=%d fail=%d total=%d\n' "$pass" "$fail" "$total"
  (( fail == 0 ))
}
run_xxhsum_tests || exit 1

