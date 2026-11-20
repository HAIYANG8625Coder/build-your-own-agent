#!/bin/zsh
# one launch only: python3 demos.py runs of episode 10 (DeepSeek). Results: demo/*.json, logs demo/*.log
cd "$(dirname "$0")"
set -a; . ~/.config/agent-series/keys.env; set +a; export PROVIDER=deepseek
[ -e demo/batch.lock ] && { echo "already launched"; exit 1; }
touch demo/batch.lock
for g in "t1 direct" "t1 inbox" "t2 stall" "t2 deny" "t2 nobody" "t3 inproject" "t3 outside"; do
  ( set -- ${=g}; for n in 1 2 3 4 5; do python3 demos.py $1 $2 $n > demo/$1-$2-$n.log 2>&1; done; touch demo/$1-$2.done ) &
done
wait
touch demo/batch.done
