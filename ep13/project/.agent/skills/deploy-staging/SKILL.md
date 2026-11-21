---
name: deploy-staging
description: Put the shop on the staging server. Use when asked to deploy, release to staging or push a build to the test server.
---
Staging deploys go through the deploy script, never by copying files by hand.

1. Run the tests. A red test stops the deploy.
2. Tag the commit: staging-YYYYMMDD-N, where N counts the deploys of that day.
3. Run: ./deploy.sh staging <tag>. The script reads the deploy key from the environment variable STAGING_DEPLOY_KEY.
4. Wait for the line "health: ok" from the script. If it says "health: failed", run ./deploy.sh rollback and report.
5. Post the tag and the time in the team channel.
6. Never deploy on Friday after 15:00.
7. The staging address is https://staging.shop.example. Check /health there after the deploy.
