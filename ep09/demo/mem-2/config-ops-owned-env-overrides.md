---
name: config-ops-owned-env-overrides
description: config.py is owned by ops, never edit; overrides use SHOP_<NAME> env vars
type: project
modified: 2026-11-20T00:18:39
---

config.py 属于 ops 团队，任何情况下都不要修改它（如 TAX_RATE、CURRENCY、VERSION 都在里面）。会变化的设置通过环境变量覆盖，命名规则 SHOP_<NAME>，例如 SHOP_TAX_RATE。
