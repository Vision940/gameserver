#!/usr/bin/env bash

# The point of this test is to ensure bash builtin fp math is being done correctly
# The game server implements its own fp math for speed and to avoid external deps

tl=$(git rev-parse --show-toplevel)
sources=(${tl}/static/client/functions/{math,logging,utility})
for s in ${sources[@]}; do
  source $s
done

echo "Unit test for static/client/functions/math started"

run_math_tests() {
  local total=0 pass=0 fail=0

  _assert() {
    local fxn=$1
    shift
    local expected=$1
    shift

    local got
    got="$($fxn $@)"
    local status=$?

    # Try to get REPLY if fxn output nothing
    [[ -z "${got:-}" ]] && {
      $fxn $@
      status=$?
      got="$REPLY"
    }

    ((total++))
    if (( status == 0 )) && [[ "$got" == "$expected" ]]; then
      ((pass++))
      printf 'ok   %-30s -> %s\n' "$*" "$got"
    else
      ((fail++))
      printf 'FAIL %-30s -> got=[%s] expected=[%s] status=%s\n' \
        "$*" "$got" "$expected" "$status"
    fi
  }

  _assert_fail() {
    local fxn=$1
    shift

    local got
    got="$($fxn $@ 2>/dev/null)"
    local status=$?

    # Try to get REPLY if fxn output nothing
    [[ -z "${got:-}" ]] && {
      $fxn $@ 2>/dev/null
      status=$?
      got="$REPLY"
    }

    ((total++))
    if (( status != 0 )); then
      ((pass++))
      printf 'ok   %-30s -> failed as expected (status=%s)\n' "$*" "$status"
    else
      ((fail++))
      printf 'FAIL %-30s -> expected failure, got=[%s]\n' "$*" "$got"
    fi
  }

  printf '\n--- fp ---\n'
  _assert __gs_fp '3'         add 1 2
  _assert __gs_fp '3.3'       add 1.1 2.2
  _assert __gs_fp '1'         add 1.25 -0.25
  _assert __gs_fp '-3.75'     add -1.5 -2.25
  _assert __gs_fp '.3'        add 0.1 0.2
  _assert __gs_fp '1.001'     add 1.000 0.001
  _assert __gs_fp '2'      -i add 1.2 0.8
  _assert __gs_fp '1'         sub 3 2
  _assert __gs_fp '-1.1'      sub 1.1 2.2
  _assert __gs_fp '1.5'       sub 1.25 -0.25
  _assert __gs_fp '-3.75'     sub -1.5 2.25
  _assert __gs_fp '.1'        sub 0.3 0.2
  _assert __gs_fp '0'         sub 5 5
  _assert __gs_fp '1'      -i sub 1.8 0.8
  _assert __gs_fp '6'         mult 2 3
  _assert __gs_fp '2.42'      mult 1.1 2.2
  _assert __gs_fp '-2.5'      mult -1.25 2
  _assert __gs_fp '.02'       mult 0.1 0.2
  _assert __gs_fp '.0001'     mult 0.01 0.01
  _assert __gs_fp '10.5'      mult 2.5 4.2
  _assert __gs_fp '10'     -i mult 2.5 4.2
  _assert __gs_fp '2'         div 6 3
  _assert __gs_fp '.5'        div 1 2
  _assert __gs_fp '.333333'   div 1 3
  _assert __gs_fp '40'        div 1.2 0.03
  _assert __gs_fp '-2.5'      div -5 2
  _assert __gs_fp '2.5'       div -5 -2
  _assert __gs_fp '3'      -i div 7 2

  printf '\n--- calc ---\n'
  _assert __gs_calc '3'              '1+2'
  _assert __gs_calc '14'             '2+3*4'
  _assert __gs_calc '20'             '(2+3)*4'
  _assert __gs_calc '1.2'            '(1+2)*4/10'
  _assert __gs_calc '7'              '3+8/2'
  _assert __gs_calc '.3'             '0.1+0.2'
  _assert __gs_calc '2.42'           '1.1*2.2'
  _assert __gs_calc '40'             '1.2/0.03'
  _assert __gs_calc '-12'            '-(1+2)*4'
  _assert __gs_calc '6'              '(-2+5)*(-3+5)'
  _assert __gs_calc '11'             '3+4*2'
  _assert __gs_calc '4.2'            '1.2+3.0'
  _assert __gs_calc '1'              '5-2*2'
  _assert __gs_calc '3.75'           '(1.25+0.25)*2.5'
  _assert __gs_calc '512'            '2^3^2'
  _assert __gs_calc '64'             '(2^3)^2'
  _assert __gs_calc '50'             '2*5^2'
  _assert __gs_calc '18'             '2*3^2'
  _assert __gs_calc '.125'           '2^-3'
  _assert __gs_calc '.25'            '4^-1'
  _assert __gs_calc '1'              '5^0'
  _assert __gs_calc '20'             '4(3+2)'
  _assert __gs_calc '21'             '(1+2)(3+4)'
  _assert __gs_calc '24'             '2(3)(4)'
  _assert __gs_calc '20'             '(3+2)4'
  _assert __gs_calc '4'              '(-2)^2'
  _assert __gs_calc '512'            '2^3^2'
  _assert __gs_calc '-8'             '-2^3'
  _assert __gs_calc '8'              '--2^3'
  _assert __gs_calc '-5'             '-(2+3)'
  _assert __gs_calc '1'           -i '0.99+0.99'
  _assert __gs_calc '1'           -i '0.6+0.6'
  _assert __gs_calc '1'           -i '0.8*2'
  _assert __gs_calc '2'           -i '0.9*3'
  _assert __gs_calc '2'           -i '(0.8+0.8)+0.8'
  _assert __gs_calc '3'           -i '(0.9+0.9)*2'
  _assert __gs_calc '1'           -i '(0.8*0.8)*3'
  _assert __gs_calc '2'           -i '(1.5*1.5)'
  _assert __gs_calc '1'  -i -r REPLY '(0.8*0.8)*3'
  _assert __gs_calc '-2.25' -r REPLY '-(1.5*1.5)'
  _assert __gs_calc '1.33'      -d 2 '4/3'
  _assert __gs_calc '1.333333'  -d 6 '4/3'
  _assert __gs_calc '1'         -d 0 '4/3'

  printf '\n--- expected failures ---\n'
  _assert_fail __gs_fp div 1 0
  _assert_fail __gs_fp mult 999999999999999999 999999999999999999
  _assert_fail __gs_fp add 9223372036854775807 1
  _assert_fail __gs_fp sub -9223372036854775808 1
  _assert_fail __gs_calc '1/0'
  _assert_fail __gs_calc '(1+2'
  _assert_fail __gs_calc '1+)2('
  _assert_fail __gs_calc 'abc'
  _assert_fail __gs_calc '2**3'
  _assert_fail __gs_calc '999999999999999999*999999999999999999'
  _assert_fail __gs_calc '2^0.5'

  printf '\nSummary: pass=%d fail=%d total=%d\n' "$pass" "$fail" "$total"
  (( fail == 0 ))
}
run_math_tests || exit 1

