# Learning and reusing app operations

`bridge learn` connects the agent's reasoning to a durable learning runtime. The
agent acquires knowledge from the app, a guide, or a demonstration and proposes
an executable procedure. The runtime records real outcomes, evaluates different
inputs, retains immutable versions, and reuses admitted skills.

```sh
bridge learn schema
bridge learn catalog
bridge learn request --file request.json
# Directly from a checkout, with no installation:
bash portable/toolkit-dispatch learn schema
```

The conductor exposes the same protocol through `learn(request={...})`. The
runtime uses Python 3.10+ and SQLite on Linux/Termux; Windows tests use WSL.
It adds no Python dependencies, makes no model API calls itself, and starts no
background worker. The existing conductor's model supplies candidate generation
and revisions within its existing budget.

**The loop**

1. Query `catalog`, then inspect a matching admitted version with `export`.
2. For a missing capability, observe the actual app/tool and propose a candidate
   with typed inputs, steps, expected outcomes and observed output paths.
3. `trial` executes one concrete attempt. Keep its request ID stable across
   transport retries. A repeated ID returns the saved result or outcome_unknown.
4. `diagnose` returns observed task evidence. Use it to distinguish environment
   failure from a procedure error, then propose a new version with `parent` set.
5. `evaluate` requires at least two distinct input sets and nonempty outcome
   assertions. It can execute reads. For mutations, supply request IDs from
   already executed trials; evaluation never repeats their effects.
6. `promote` admits only a version that passed every case. Revisions retain
   unchanged regression cases. `execute` then applies it to a new task.

Two passing cases are an admission minimum, not proof of broad generalization.
The [experiment](docs/research/learning-experiment-01.md) measures actual transfer.

**Skill format**

```json
{
  "id": "read-hidden-app",
  "description": "Read current text from a hidden app workspace",
  "tags": ["phone", "read"],
  "inputs": {
    "display": {"type": "string"},
    "package": {"type": "string"}
  },
  "plan": {
    "task": {"goal": "Read {{package}} on {{display}}"},
    "steps": [{
      "adapter": "hidden", "verb": "observe", "target": "hidden:{{display}}",
      "args": {},
      "expect": {"equals": {"screen.package": {"$input": "package"}}}
    }]
  },
  "outputs": {"text": "0.screen.text", "nodes": "0.screen.nodes"}
}
```

`{{name}}` interpolates a scalar into a string. `{"$input":"name"}` preserves
its type. Neither evaluates code. Input types are string, integer, number,
boolean, array and object; optional declarations include default and enum.
Output paths address actual verified step results, numbered from zero. Inline
credentials are rejected; secret references in task plans remain supported.

Send one JSON request per call. `propose` takes the complete object above in
`spec`; optional `sources` must be real task IDs. A revision adds `parent`.

```json
{"operation":"trial","id":"read-hidden-app","version":1,"inputs":{"display":"main","package":"com.example"},"request_id":"attempt-001"}
{"operation":"diagnose","task_id":"skill-task-..."}
{"operation":"export","id":"read-hidden-app","version":1}
```

An evaluation case contains `id`, `inputs`, and `expect`, for example
`{"id":"first","inputs":{"display":"main","package":"com.example"},"expect":{"contains":{"text":"Expected record"}},"request_id":"attempt-001"}`.
The evaluation request has operation=evaluate, id, version, and a cases array.
Omit request_id only for automatic read-only cases. Expected outcomes must come
from the task, not be rewritten after a failure to make the score pass.

```json
{"operation":"promote","id":"read-hidden-app","version":1}
{"operation":"execute","id":"read-hidden-app","inputs":{"display":"main","package":"com.example"},"request_id":"next-real-task"}
```

A crash or lost reply can leave outcome_unknown. Inspect the destination and
recorded evidence before issuing a new request ID. This does not promise
exactly-once effects for arbitrary third-party apps.

**Phone actions**

One shared reader serves every display. `snapshot.json` includes display ID,
generation, revision, observation time, node states, and packages. `observe`
rejects stale/invalid snapshots. Actions require one exact enabled, visible node
in the selected package plus a postcondition describing the expected content.
Supported actions: observe, open, click, set_text, scroll_forward, scroll_backward.
Selectors combine exact text, description, resource_id or token. Text entry uses
Android's accessibility action, preserving Unicode and punctuation.

```json
{
  "adapter":"hidden", "verb":"set_text", "target":"hidden:main",
  "args":{"package":"com.example","selector":{"resource_id":"com.example:id/search"},"text":"new query"},
  "expect":{"contains":{"screen.text":"new query"}}
}
```

`open` takes args.app as an Android package/component and needs a screen
postcondition. A single-instance app may move its existing task; virtual displays
share app/account state. Post-action waiting never repeats a dispatch.

**Existing tools**

The `toolkit` adapter calls existing bridge tools with exact argument arrays.
For example, target=`toolkit:jobs`, verb=`run`, args.arguments=
`["find","--top","5"]`. Results expose stdout, stderr, exit_code and parsed
JSON as payload. Use a specific result expectation established from the real
operation. Recursive learn/checkpoint calls are excluded. Other existing adapters
remain available subject to their actual supported actions.

**Build and checks**

```sh
python3 tools/hidden-display/build_reader.py --check
bash tests/test_learning_dispatch.sh
python3 -m unittest discover -s tests -p test_learning_conductor.py -v
(cd runtime/task-engine && python3 -m unittest discover -s tests -v)
```

The reader build is pinned to JDK 21, Android API 36 and build-tools 36.0.0.
`--check` rebuilds and compares the exact dex bytes. State remains in the existing
private task-engine database outside the repo. Never commit real task recordings
or private data as sample fixtures. Use a separate phone checkout if its current
source has local changes.

The [research blueprint](docs/research/hidden-screen-learning.md) describes later
capabilities: broader app acquisition, cross-device composition, autonomous
curricula and model transfer. The first release implements the executable skill
lifecycle; those broader experiments have not been run.