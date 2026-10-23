# Railway production deploy branch

`GET /api/build-info` on **blackdark.io** reports `git_branch` and `git_commit` for the running image.

Production has historically tracked **`cursor/launch57-phase8-launch-coherence-358c`**, not `main`. Merges to `main` alone do not update the live site until this branch (or Railway service settings) is updated to include those commits.

After deploy, verify:

```bash
curl -sS https://blackdark.io/api/build-info | jq '.git_commit,.owner_admin_registered'
curl -sS -o /dev/null -w '%{http_code}\n' -H 'X-Admin-Key: invalid' https://blackdark.io/admin
# expect owner_admin_registered true and HTTP 403 (not 404)
```
