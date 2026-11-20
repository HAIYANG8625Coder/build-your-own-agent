#!/bin/zsh
# one launch only: python3 demos.py runs of episode 11 (DeepSeek). Results: demo/*.json, logs demo/*.log
cd "$(dirname "$0")"
set -a; . ~/.config/agent-series/keys.env; set +a; export PROVIDER=deepseek
[ -e demo/batch.lock ] && { echo "already launched"; exit 1; }
mkdir -p demo; touch demo/batch.lock
for g in "t1 none" "t1 all" "t1 lazy" "t2 control" "t2 plain" "t2 rule" "t2 gate"; do
  ( set -- ${=g}; for n in 1 2 3 4 5; do python3 demos.py $1 $2 $n > demo/$1-$2-$n.log 2>&1; done; touch demo/$1-$2.done ) &
done
wait
touch demo/batch.done
