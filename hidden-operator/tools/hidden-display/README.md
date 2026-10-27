# Hidden Display — screens only the agent can see

Runs an app on a **private, always-on virtual display** the phone's physical panel
never shows, so the agent can drive that app (see + tap) **while the owner uses the
real screen** for something else. No root. No scrcpy. Verified on SM-F766U / Android 16.

**Many at once.** Start several named screens — a *crew* of invisible phones out of one
phone (e.g. apply to several jobs in parallel). Each screen has its own name, size, and
id; pick one with `-n <name>`. A screen can be **phone**-shaped or **tablet**-shaped —
a tablet screen makes apps show their wide, two-pane layout (more on screen, fewer taps).

## Why
The original accessibility route read only the default display. The shared UD
reader now reads hidden displays through `OWN_FOCUS` and `getWindowsOnAllDisplays()`.
An app must be **foreground** on some display to be operated. So to work an app-only
service (WhatsApp, a native app) *without* stealing the owner's screen, the app needs
its **own** foreground — a display the owner doesn't see. Websites don't need this
(the hidden Chromium already runs them headless); this is for **app-only** work.

## How it works
- `vd.dex` (source `VD.java`) runs at **shell uid** (adb/Shizuku — which holds
  `ADD_TRUSTED_DISPLAY` on Android 14+) and calls
  `DisplayManager.createVirtualDisplay(...)` with `PRESENTATION | TRUSTED |
  SHOULD_SHOW_SYSTEM_DECORATIONS | CAN_SHOW_WITH_INSECURE_KEYGUARD`, backed by an
  **ImageReader** surface. That display can host other apps (`am start --display <id>`)
  and every frame is capturable. The owner-uid check requires the caller's package to
  match the uid, so the holder builds its context as `com.android.shell` (a naive call
  throws *"packageName must match the owner uid"*).
- **Works while the phone is locked.** The `CAN_SHOW_WITH_INSECURE_KEYGUARD` flag is
  what lets an app launch + draw on the display when the lock screen is up. Without it,
  `am start --display` is denied with a `SecurityException` the moment the phone locks —
  so the hidden lane would only work while the owner had the phone unlocked. That flag
  is **incompatible with `PUBLIC`** ("Public display must not be marked as
  SHOW_WHEN_LOCKED_INSECURE"), so we drop `PUBLIC` and match the real cover display's set.
- Each screen writes its id + frames under its own folder `/data/local/tmp/vd/<name>`,
  so many holders run side by side; liveness is tracked by the logical display id
  (`dumpsys display` → `mDisplayId=`), not by the shared display name.
- **Eyes:** the accessibility tree does **not** cross to a non-default display
  (measured), so this drives by **picture** — `shot` captures one frame on demand
  (idle otherwise; no constant polling).
- **Hands:** `input -d <id> tap` reaches the hidden display (works even though it
  reports `touch NONE`).

## Use
```sh
bash scripts/hidden_display.sh start                 # default screen "main" (phone size); prints the id
bash scripts/hidden_display.sh launch com.whatsapp   # run an app on it (owner's screen untouched)
bash scripts/hidden_display.sh shot out.png          # one frame -> PNG (needs python3 + pillow)
bash scripts/hidden_display.sh grid 100 out.png      # frame + labeled grid (numbers = real tap coords)
bash scripts/hidden_display.sh zoom 160 1580 130 4   # look closer: crop+enlarge+grid around a point
bash scripts/hidden_display.sh tap 160 1580          # tap it (coords read from the grid/zoom)
bash scripts/hidden_display.sh status|id|stop

# a crew of screens (each -n <name>), and a tablet-shaped one:
bash scripts/hidden_display.sh start  -n tablet tablet          # 1600x2560@320 → wide layouts
bash scripts/hidden_display.sh start  -n job2                   # another phone screen
bash scripts/hidden_display.sh launch -n tablet com.linkedin.android
bash scripts/hidden_display.sh shot   -n tablet out.png
bash scripts/hidden_display.sh list                            # every screen: name, id, up/down
bash scripts/hidden_display.sh stop -n job2                    # stop one
bash scripts/hidden_display.sh stopall                         # stop them all
```
`start` sizes: `phone` (1080×2400@420, default), `tablet` (1600×2560@320), or explicit `W H DPI`.

### The zoom trick — see the exact spot before you tap
Driving by picture, it's easy to be a few pixels off (tap the 4, not the 7). The fix
is **coarse → fine**, the same "adaptive zoom-in" the GUI-grounding papers use — except
the agent's own eyes are the grounding, so there's no extra model, no GPU, no API cost:
1. `grid` — a labeled grid over the whole frame. Every pink number is a **real tap
   coordinate**. Read where the target roughly is.
2. `zoom <cx> <cy> [radius=120] [scale=4]` — crop a box around that point, blow it up,
   and lay the same real-coordinate grid on it, with a crosshair on the aim point. The
   true centre of the button is now obvious.
3. `tap <x> <y>` — tap the centre you just read.

Because the grid labels are always in the **original** display coordinates (never the
zoomed pixels), the number you read off a 4× zoom is the exact number you pass to `tap`.
`activate` (re)starts it if down — called by `ACTIVATE_ANDROID_NODE.sh` and the watchdog,
so it wakes on reboot with the rest of the door-set.

## Shared accessibility reader

`UD daemon all /data/local/tmp/vd` owns one UiAutomation connection for all named
displays. Its snapshots are versioned; empty reads invalidate old targets. The
learning adapter dispatches unique-node accessibility actions through correlated
JSON requests. Existing accessibility services remain enabled through connect
flag 0x1. See [LEARNING.md](../../LEARNING.md) for the supported command protocol.

Rebuild `ud.dex` with `python3 tools/hidden-display/build_reader.py` using JDK 21,
Android API 36 and build-tools 36.0.0. Add `--check` to verify the committed bytes.

## Rebuild the display holder dex (only if VD.java changes)
Needs a JDK + Google's `r8.jar` (has D8). `VD.java` touches the framework almost
entirely by reflection, so you don't need a full `android.jar` — four tiny **compile
stubs** are enough (`android.os.Looper`, `android.os.Handler`, `android.content.Context`,
`android.view.Surface`, with the exact signatures VD calls). Build the stubs, compile
VD against them, then D8:
```sh
javac -d sout stubs/android/**/*.java            # the 4 stub classes
javac -cp sout -d cout VD.java                   # -> VD.class, VD$1.class
jar cf stubs.jar -C sout .
java -cp r8.jar com.android.tools.r8.D8 --min-api 34 --lib stubs.jar --output dout cout/*.class
cp dout/classes.dex vd.dex
```
The stubs are compile-time only (never in the dex); the real framework classes resolve
at runtime. The committed `vd.dex` is prebuilt, so a device needs **no** toolchain —
the script just pushes it.

## The one rule that must never be broken (2026-09-19)

The reader daemon holds a **UiAutomation**. Android unbinds **every accessibility
service on the whole phone** while a UiAutomation is registered with `flags=0` —
TalkBack, the portal, and WiM's text injector all go dead, while their switches in
Settings still read **ON**. That is why WiM stopped typing on 2026-09-19: nothing
was wrong with WiM.

So `UD.java` connects with `flags = FLAG_DONT_SUPPRESS_ACCESSIBILITY_SERVICES (0x1)`.
Never connect without it. Checks:

```sh
adb shell 'dumpsys accessibility | grep "^Ui Automation\["'   # a holder exists
adb shell 'dumpsys accessibility | grep "Bound services"'      # must NOT be empty
scripts/hidden_display.sh reap                                 # free a stuck phone
```

The daemon also writes `$DIR/ud.pid` and exits by itself ~1s after its screen dir is
deleted, so `stop`/`stopall` can never strand a holder again.

## Limits (honest)
- Driven by picture, so a step costs a screenshot + a look — slower than the
  default-screen word-reader, fine for form-filling / applying.
- The display id changes each start; always read it via `hidden_display.sh id [-n name]`.
- Reboot-volatile (the virtual display + holder die on reboot); the boot-heal
  re-creates the default `main` screen (extra named screens are on-demand).
- **Single-instance apps:** some apps refuse to run in two places at once. If the owner
  has the app open on the real screen, launching it on a hidden screen may move it, not
  clone it. Untested per-app; try before relying on it for a specific app.
- RAM is the ceiling on how many screens run at once.
