#!/bin/zsh
# one launch only: 4 tasks x 2 setups x 5 trials (DeepSeek). Results: demo/*.json, logs demo/*.log
cd "$(dirname "$0")"
set -a; . ~/.config/agent-series/keys.env; set +a; export PROVIDER=deepseek
[ -e demo/batch.lock ] && { echo "already launched"; exit 1; }
mkdir -p demo; touch demo/batch.lock
for g in "version base" "version check" "tax base" "tax check" "discount base" "discount check" "readonly base" "readonly check"; do
  ( set -- ${=g}; for n in 1 2 3 4 5; do python3 eval.py run $1 $2 $n > demo/$1-$2-$n.log 2>&1; done; touch demo/$1-$2.done ) &
done
wait
touch demo/batch.done
