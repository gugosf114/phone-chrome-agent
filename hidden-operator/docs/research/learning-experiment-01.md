# Experiment 01: does Agent Bridge learn a reusable capability?

Proposed experiment, not executed. Companion to RESEARCH-AND-BLUEPRINT.md. All thresholds below are engineering targets selected for this project; they are not results from the cited literature.

**Question**

Does a fixed model equipped with skills learned from actual interaction solve new tasks better than the same model using either no persistent skills or static recipes? Does the gain survive different data, starting states, and task combinations?

**The first product-shaped outcome**

Teach Agent Bridge to collect a set of records from a native app, transform them into a local artifact, and use the artifact in another app. On an unseen request it must read current records, use the requested date range, handle similarly named entities, and return a verifiable result. The typed capability is `collect_records(query, date_range)`; the consumer might create a note or draft calendar entry from those records.

The app need not have an API. The learned operation wraps its interface and returns structured output plus evidence. Completion means the requested artifact or app state exists with the correct values, not that all taps returned successfully.

**Test environment**

Use a resettable Android emulator with synthetic records and three controlled app categories: notes/records, calendar/tasks, and file/export. Begin with benchmark-compatible apps from AndroidWorld where practical. Pin package versions and layouts before collecting data. The harness must demonstrate reset, setup, and outcome reading for each chosen app before a learning run counts.

After the emulator experiment passes, repeat a bounded subset on a hidden display on the physical Samsung, with the same pinned app builds and dedicated test data. This is a transfer test. Emulator scores do not count as evidence of Samsung compatibility.

The first implementation must provide a single shared observer, fresh state, correct exit/error reporting, and observed completion checks to EVERY comparison arm. Otherwise differences in a broken executor could masquerade as learning. Keep the earlier reliability repairs narrow and in service of this experiment.

**Data split**

- Twelve library-building instances: four per app category. Collect demonstrations, successful attempts, failures, and observed outcome evidence here.
- Thirty held-out evaluation instances: twelve change the records or input values, six change presentation, six change initial state or add an interruption, and six compose operations across apps.
- Held-out tasks are authored and frozen before learning. Their answers, scoring rules, and output fixtures are not available to the skill writer.
- At least eight previously solved library-building cases form a regression set. These measure retention, not generalization.

Presentation changes must be supported by the chosen apps, such as font scaling or theme. State changes can include starting from another page, an empty result, a duplicate record name, or a supported modal. Do not fabricate impossible states and then count them as agent failures.

**Three comparison arms**

| Arm | Persistent material available | What changes during library construction |
|---|---|---|
| A: no learning | Normal tool descriptions and the current task | No skill library |
| B: static recipe | A recipe distilled from the same training evidence | Initial recipe only |
| C: evidence-based learning | Versioned skill packages built from the same evidence | Candidate revisions can be proposed, tested on training/validation cases, and accepted |

Use the same base model, temperature policy, tool implementations, initial device snapshots, and per-evaluation action/time limits. Freeze the libraries before evaluating held-out cases. The primary held-out test permits normal replanning but no persistent learning from those held-out results. A separate online-learning experiment can follow afterward.

Fix an initial ceiling of 50 dispatched UI/tool actions and 10 minutes per task, shared by all attempts for that task. A model token/inference budget must also be identical across arms. The ten-run calibration chooses the actual token cap before the evaluation begins; record the value in the run manifest and do not tune it after seeing scores. These ceilings may be revised in a new, separately labeled experiment if they make valid tasks impossible.

The small pilot uses six held-out instances, three arms, two repeats: 36 scored runs. Use it to find harness defects and estimate cost, not to claim statistical proof. The expanded study uses all thirty instances, three arms, three repeats: 270 scored runs. Randomize execution order and restore initial state each time.

**What each skill contains**

```text
skill_id and version
purpose and applicability
input schema and output schema
app/package version and workspace requirements
required state and exclusive resources
program or workflow, including live-state branches
completion predicates and outcome evidence requirements
recovery behavior, including outcome_unknown
source episode references and documentation provenance
training/validation tests and failure cases
measured results, cost, and parent version
```

A demonstration supplies evidence; it does not specify all invariants automatically. Candidate generation must separate variable facts from procedural rules. Changing a date, person, filename, or account in the test should not accidentally reuse the demonstration's values.

**Evidence and scoring**

Every episode records the task ID, environment version/reset ID, model/version, skill versions, observation revision, input action, resulting state, verifier result, duration, and model usage. Save screenshots at consequential transitions and failures, not an unlimited stream. Redact secrets and irrelevant private content from reusable skill material.

Prefer deterministic checks against test-app state, files, or a controlled service. For example, the exported CSV must contain exactly the expected records and date range; the created entry must match its title, time, and source ID. A model may help diagnose an error but does not supply the only success score.

Score these separately:

- Complete task success.
- Wrong or duplicate effects, including changes to records outside the requested set.
- Correct recognition of an uncertain outcome after interrupted acknowledgement.
- UI/tool actions, wall-clock time, model tokens, and measured cost per verified result.
- Skill retrieval success and failure by task family.
- New-data, new-layout, new-start-state, and composition success rates.
- Regression against the retained cases.

Report per-task paired results and uncertainty. Do not pool repeats as if they were independent new task definitions. Use paired bootstrap intervals across task IDs for a modest indication of score uncertainty; a small pilot remains a pilot.

**Promotion rule for the first milestone**

The full C arm should achieve at least 70% verified completion across the held-out set and improve over A by at least 20 percentage points. It should outperform B on the perturbed-state subset, lose no more than five percentage points on the regression set, and produce zero wrong-record or duplicate irreversible test effects. These are proposed targets, not assurances that the system will meet them.

A failed target is information. If C only improves exact repeats, it has learned a narrow replay pattern. If C beats A but not B, iterative revision has not earned its cost. If C improves but inference costs rise substantially, calculate whether repeated reuse amortizes construction and diagnosis. Include learning cost at explicitly stated reuse counts, such as 10, 100, and 1,000 uses; do not hide unsuccessful training attempts.

Stop a run when the action/time/budget limit is reached. Record the observed failure. A missing transport or unsupported app reset is an environment error and should be reported separately, without silently removing difficult cases from the denominator.

**The next experiments, after the core comparison**

1. **Model portability:** keep the admitted library fixed, change the planner model, and repeat twelve representative held-out tasks. Compare the replacement model with and without the library. This tests whether knowledge survives model replacement; do not compare different models and attribute the entire difference to learning.
2. **New app acquisition:** introduce a fourth app, expose the same documentation and demonstration inputs to all arms, and allow a fixed exploration budget before six unseen target tasks. This separately tests learning a missing operation, rather than only reusing familiar operations.
3. **Guide versus demonstration:** compare a human-written guide, a recording, both, and neither under matched inference budgets. Distinguish same-task guidance from a recording of a related task.
4. **Repair:** change a supported layout or app version, allow learning from separate repair cases, then evaluate on fresh variants plus the old regression set.
5. **Cross-device composition:** a phone skill produces a typed record set; an existing Windows/browser adapter consumes it. Score the final artifact and data lineage.
6. **Parallel work:** only after single-run validity, run independent app tasks on two displays, verify user-screen noninterference and accessibility-service continuity, and account for shared app/account resources. This is an optional later operator-enabled test.

**Implementation order and ownership**

One implementation can build this sequentially; parallel agents are not required.

- Add an episode writer and deterministic fixture/verifier harness.
- Add a hidden-screen adapter to the task engine and a versioned observation/action contract.
- Implement a small skill schema plus runtime validation and exact metadata retrieval.
- Implement A and B before adding revision, so there is a real baseline.
- Add candidate generation, a separate-context failure analyst, and a restricted revision interface.
- Implement evaluation and promotion with immutable held-out scoring material.
- Run the pilot, inspect all failures, freeze a new manifest if harness changes are necessary, then run the expanded comparison.

Suggested deliverables are an episode JSONL, a SQLite skill registry, filesystem skill packages, an evaluation manifest, per-task results, and a short result report. Use the repository's existing task/resource lock and checkpoint primitives where appropriate. The original bridge transport scripts stay untouched.

**Compute and budget**

No weight training is required for this experiment. Establish environment-host capacity first; the current laptop's ability to run an emulator has not been tested in this research turn. A remote emulator host is an alternative to quote if local capacity is insufficient.

The proposed $50 pilot and $250 expanded-study allowances in the main blueprint are spending ceilings to choose, not vendor estimates or authorization already used. Calibrate with ten runs, forecast using observed token/image usage and current provider prices, and stop before the selected cap. No paid model calls or device experiments were performed for this document.

**The decision this experiment enables**

If it passes, build capability acquisition and cross-device composition next. If it fails, the breakdown identifies whether to invest in the observer, executor, knowledge representation, retrieval, or verifier. Either outcome gives Agent Bridge a reusable evaluation foundation and a precise account of what it can currently learn.
