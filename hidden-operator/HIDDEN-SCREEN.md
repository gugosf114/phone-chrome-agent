# Hidden Screen Operator

**Drive the phone on screens only the agent sees.** One real phone. Extra
displays the physical panel never shows. The agent opens an app on a hidden
screen, reads its buttons *by name*, and taps them — while the owner keeps using
the real screen. No root, no scrcpy.

This page is the one place for all of it: the invisible screens, driving an app
by name, many screens at once, the never-die keeper, and the photo fallback.
Pointing another model here? Say: *"agent-bridge, the Hidden Screen Operator —
start at HIDDEN-SCREEN.md."*

**Executable learning:** see [LEARNING.md](LEARNING.md) for `bridge learn`.
It records actual attempts, stores parameterized skill versions, evaluates new
inputs, preserves regression cases and reuses admitted skills. The conductor
exposes the same protocol. One shared reader serves all named displays, with
fresh observations and semantic node actions in this new path.

## What it does
- **Invisible screens.** Make one or many private displays the owner never sees.
- **Drive by name.** Find a button by its label ("plus", "send") and tap it —
  straight from the app's own accessibility tree, exact centre, ~0.8s per tap.
- **Many named workspaces.** Displays share one phone and its app/account state.
- **Recovery.** A keeper holds the screens up; if the OS reaps one, it comes
  back on its own in seconds and re-opens its app. Verified: back in ~6s.
- **Recorded tasks.** `bridge learn` uses the task engine's evidence and
  checkpoints. Repeating a request ID never redispatches it. The older
  `hidden_drive.sh run` replays steps and is a legacy path, not a durable journal.
- **Photo fallback.** For apps that expose no names: teach once by screenshot,
  replay by template match.

## The pieces
| File | Job |
|------|-----|
| `scripts/hidden_display.sh` | Make / hold / stop the invisible screens; shot, tap, launch, `ensure` (heal) |
| `scripts/hidden_drive.sh` | Drive an app by name: `open` / `do` / `seq` / `run` / `type` / `key` / `read` |
| `scripts/hidden_supervisor.sh` | The keeper — wake-lock + phantom-off + 3s watch loop + reboot job |
| `scripts/ui.sh` | Read the screen (the accessibility tree) by name |
| `scripts/app_map.py` | Map an app's screens by name |
| `tools/hidden-display/VD.java` + `vd.dex` | The display holder (creates the virtual display) |
| `tools/hidden-display/UD.java` + `ud.dex` | The resident reader daemon (writes the button list) |
| `tools/hidden-display/frame_to_png.py` | Turn a captured frame into a PNG |
| `tools/hidden-display/match.py` + `TEACH.md` | The photo-match fallback (teach once, replay) |
| `scripts/boot/start-agent-bridge` | Boots the keeper at phone start |
| `ACTIVATE_ANDROID_NODE.sh` | Activates the lane by hand (reboot-heal, boot the keeper) |

## Run it
```sh
# make a hidden screen, open the calculator on it
scripts/hidden_display.sh start  -n main phone
scripts/hidden_display.sh launch -n main com.sec.android.app.popupcalculator/.Calculator

# drive it by name
scripts/hidden_drive.sh seq  main 7 plus 8     # -> 15, on a screen you can't see
scripts/hidden_display.sh shot -n main proof.png # screenshot the invisible screen

# keep it alive on its own
scripts/hidden_supervisor.sh boot              # wake-lock + self-heal watch loop
```

## Status
- The learning runtime has automated unit/integration tests and a reproducible
  reader build. Its real-device and held-out-task results must be recorded
  separately; the historical calculator result below is not a learning benchmark.
- **Proven live** on SM-F766U (Android 16): drove a hidden calculator by name
  (7 + 8 = 15); killed the display holder → keeper self-healed in ~6s and
  re-opened the app; the owner's accessibility service (WiM) stayed intact.
- **In the repo, on `main`** (PRs #13–#23).
- **Not auto-running on the phone by default** — it runs on demand. To make it
  always-on: put the phone's runtime checkout on `main` and enable the boot
  starter (`~/.termux/boot/start-agent-bridge`, currently parked as `.off`).
