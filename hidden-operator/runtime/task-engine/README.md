# Agent Bridge task engine

This is Agent Bridge's built-in checkpoint, proof, resume, and replay engine.

George gives it a goal, a permission level, a target box, and a duration. The
engine checks that whole box before the first action. It then uses the fastest
available hand, saves the exact checkpoint after every successful step, checks
the result, and records the time. A newer permission takes effect before the
next step.

One task has one live runner. A second agent cannot replay the same checkpoint
concurrently. The operating system releases its task lock when the engine
process exits, so abandoned work is recoverable immediately.

## Permission levels

| Level | Meaning |
| --- | --- |
| 0 | Talk only. |
| 1 | Read only. |
| 2 | Read and create new downloads. |
| 3 | Make local changes. |
| 4 | Make the named outside changes. |
| 5 | Full authority inside the named task and targets. |

Scopes are `answer`, `test`, `turns`, `session`, `task`, and `standing`.
Permission expires with its scope. A later permission replaces the earlier one.

## Real hands

- `phone` calls the already-paired Agent Bridge MCP server at
  `http://127.0.0.1:8080/mcp` and binds permission to the whole
  `phone:george` device target.
- `browser` uses the existing `browser-runner` daemon. Every browser plan must
  name `phone-headless`, `android-chrome`, `laptop-chrome`, or `cdp`; there is no
  hidden default or fallback. The chosen route appears in preflight, status,
  proof events, and the final result. Protocol-v2 readiness and an opaque
  exact-page token reject a stale
  runner or a tab that changed between planning and execution without logging a
  private URL. Upload and Ashby permissions also name every exact local source
  file, so destination-origin authority cannot silently authorize another
  document.
- `google-console` reuses the existing Analytics and Search Console runtime and
  binds permission to `google-console:george`.

Phone and Google Console reads remain installed. Their mutations fail preflight
until those runtimes return intrinsic post-action proof; a command-completed
response is not accepted as evidence that the requested change occurred.
Generic form changes, uploads, click, keypress, reload/back, tab, frame, and
JavaScript actions are also preflight-disabled because browser-local state
cannot prove or safely replay their outside effects. The Ashby lane uses its
durable operation-specific verifier.

Arbitrary local processes are excluded from the installed adapter set because
an executable path does not confine what the process can read, change, or send.

## Fast path

A plan may name `recipe_key`. Every verified success saves its steps. `replay`
runs that path directly without asking a model to rediscover the clicks.

```sh
bridge checkpoint race-start --goal "Open and verify the page"
bridge checkpoint check examples/browser-public-read.json
bridge checkpoint run examples/browser-public-read.json
bridge checkpoint benchmark examples/browser-public-read.json --warmup 1 --runs 5
bridge checkpoint status TASK_ID
bridge checkpoint events TASK_ID
bridge checkpoint resume TASK_ID
bridge checkpoint replay RECIPE_KEY NEW_PERMISSION.json --browser-backend ROUTE
bridge checkpoint permit TASK_ID NEW_PERMISSION.json
bridge checkpoint revoke TASK_ID
```

## Speed rule

Set `baseline_ms` to George's manual time. Set `speed_ratio` to the fraction the
agent must beat. A completed task that misses the limit is reported as
`completed_slow` and exits with code 4.

For a new model-planned task, run `race-start` as the first tool action and put
its ID in the plan as `race_ref`. The result then separates execution time from
planning-and-wait time and judges the full request-to-result time. `benchmark`
measures the saved executor by itself.

The runner keeps Playwright and the authenticated browser connection warm.
`benchmark` accepts read-only plans only. Mutating work runs once and uses its
real request clock; timing never repeats a send, submission, or outside change.

## Install

Install `browser-control/` first so `browser-runner-daemon` is available, then
run:

```sh
bash runtime/task-engine/install-phone.sh
```

The public front door is always `bridge checkpoint`. No separate model skill or
standalone command is installed.

State and proof live in
`~/.local/state/agent-bridge/task-engine.sqlite3`. The database is mode `0600`.
Inline secrets are rejected at parsing and again at the database boundary.
Plans and recipes store `$secret_env` or
`$secret_file` references and resolve them only at execution time.
