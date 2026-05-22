---
description: Stage all changes (skipping secrets), commit with a generated message, and push to the current branch.
argument-hint: [optional message hint]
allowed-tools: Bash(git status *) Bash(git diff *) Bash(git log *) Bash(git add *) Bash(git commit *) Bash(git push *) Bash(git rev-parse *)
---

Stage the current working changes, commit them, and push to the current branch.

Follow these steps in order.

## 1. Inspect repository state

Run these in parallel:
- `git status` — all changed and untracked files. Never use the `-uall` flag.
- `git diff HEAD` — full content of staged and unstaged changes.
- `git log -5` — learn this repo's commit-message style.

## 2. No-changes guard

If `git status` shows nothing to commit, print `Nothing to commit — working tree clean.` and stop. Do NOT create an empty commit.

## 3. Secret scan

From the changed and untracked files, identify any file matching these patterns and EXCLUDE it from staging:
- `.env`, `.env.*`
- `*.pem`, `*.key`, `*.p12`, `*.keystore`
- `*credentials*`
- `id_rsa`, `id_dsa`, `id_ecdsa`, `id_ed25519`

Remember every excluded file — they are reported in step 6 as "skipped (possible secret)".

## 4. Stage

Run `git add` naming every non-excluded changed and untracked file explicitly. Do NOT use `git add -A` or `git add .`.

## 5. Draft the commit message

Match the conventional-commit style seen in `git log` (`feat:`, `fix:`, `chore:`, `docs:`, etc.). Keep the summary line under ~72 characters and focused on the "why".

- If `$ARGUMENTS` is non-empty, use it as a steer for the message — it is a hint, not the literal message text.
- If `$ARGUMENTS` is empty, generate the message entirely from the diff.
- End the message with this trailer:

  ```
  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  ```

## 6. Show the plan

Print:
- Files staged (each path).
- Files skipped as possible secrets, if any.
- The full commit message.

## 7. Commit and push (auto-run — no approval needed)

- Create the commit, passing the message via a HEREDOC:

  ```bash
  git commit -m "$(cat <<'EOF'
  <summary line>

  <body>

  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  EOF
  )"
  ```

- Push: run `git push`. If it fails specifically because the branch has no upstream (error contains "has no upstream branch"), run `git push -u origin HEAD`.
- Never use `--force`, `--no-verify`, or `--no-gpg-sign`.

## 8. Push failure handling

If the push is rejected for any other reason (e.g. non-fast-forward — "Updates were rejected"), print the exact error and stop. Do NOT force-push and do NOT try to resolve it automatically — tell the user to pull/rebase first.

## 9. Report

Print the new short commit hash (`git rev-parse --short HEAD`) and confirm the push succeeded, naming the branch.
