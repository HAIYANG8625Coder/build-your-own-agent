#!/bin/zsh
# one launch only: episode 13 real runs (DeepSeek). Phase A runs in parallel (T1, T3, T4); phase B (T2, timing) runs one at a
# time, stream and plain taking turns, so the API load is the same for both. Results: demo/*.json, logs demo/*.log
cd "$(dirname "$0")"
set -a; . ~/.config/agent-series/keys.env; set +a; export PROVIDER=deepseek
[ -e demo/batch.lock ] && { echo "already launched"; exit 1; }
mkdir -p demo; touch demo/batch.lock
for g in "t1 kept" "t1 fresh" "t3 repair" "t3 control"; do
  ( set -- ${=g}; for n in 1 2 3 4 5; do python3 demos.py $1 $2 $n > demo/$1-$2-$n.log 2>&1; done; touch demo/$1-$2.done ) &
done
( for n in 1 2 3 4 5; do python3 demos.py t4 $n > demo/t4-$n.log 2>&1; done; touch demo/t4.done ) &
wait
for n in 1 2 3 4 5; do for m in stream plain; do python3 demos.py t2 $m $n > demo/t2-$m-$n.log 2>&1; done; done
touch demo/batch.done
