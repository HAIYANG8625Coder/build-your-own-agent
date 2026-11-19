---
name: config-py-owned-by-ops
description: config.py belongs to the ops team and must never be edited
type: project
modified: 2026-11-20T00:11:31
---

In the shop project, config.py is owned by the ops team: never edit it. Settings that change are overridden via environment variables named SHOP_<NAME>, e.g. SHOP_TAX_RATE.
