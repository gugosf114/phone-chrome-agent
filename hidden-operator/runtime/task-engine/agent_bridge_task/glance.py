"""One fast look when a saved step meets a live page.

The saved button name is the deal. Extra buttons do not matter while that
button is still on the page. A missing or doubled name stops the click.
A later repair may change only the broken step.
"""
from __future__ import annotations

import copy
from typing import Any


def _label(control: dict[str, Any]) -> str:
    for key in ("text", "label", "name", "description"):
        value = control.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def press_or_stop(
    wanted: str,
    controls: list[dict[str, Any]],
    backups: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    """Press the learned button if it is still on the page. Otherwise stop."""
    if not isinstance(wanted, str) or not wanted.strip():
        raise ValueError("need the button the task learned")
    if not isinstance(controls, list):
        raise ValueError("need the live page buttons")
    names = [wanted.strip()]
    for backup in backups:
        if isinstance(backup, str) and backup.strip():
            names.append(backup.strip())
    seen: set[str] = set()
    ordered: list[str] = []
    for name in names:
        key = name.casefold()
        if key not in seen:
            seen.add(key)
            ordered.append(name)
    for name in ordered:
        hits = [
            control
            for control in controls
            if isinstance(control, dict) and _label(control).casefold() == name.casefold()
        ]
        if len(hits) > 1:
            return {
                "action": "stop",
                "reason": "the old button appears more than once",
                "page": controls,
            }
        if len(hits) == 1 and isinstance(hits[0].get("id"), str) and hits[0]["id"]:
            return {
                "action": "press",
                "control": hits[0],
                "matched": name,
                "extra": len(controls) - 1,
            }
    return {"action": "stop", "reason": "the old button is gone", "page": controls}


def critic_packet(
    instruction: str,
    observations: list[Any],
    actions: list[Any],
) -> dict[str, Any]:
    """What a later look may see. The saved plan stays out of this packet."""
    if not isinstance(instruction, str) or not instruction.strip():
        raise ValueError("need the task")
    if not isinstance(observations, list) or not isinstance(actions, list):
        raise ValueError("need the pages and the action trace")
    return {
        "instruction": instruction,
        "observations": observations,
        "actions": actions,
    }


def name_break(actions: list[dict[str, Any]]) -> dict[str, Any]:
    """Name the first step in the trace that did not go through."""
    if not isinstance(actions, list):
        raise ValueError("need the action trace")
    for index, item in enumerate(actions):
        if not isinstance(item, dict):
            return {"step": index, "cause": "this step missed"}
        status = item.get("status")
        if status in {"ok", "progress", "success", "pressed"} or item.get("ok") is True:
            continue
        cause = item.get("cause") or item.get("error") or "this step missed"
        return {"step": item.get("step", index), "cause": cause}
    return {"step": None, "cause": "no break"}


def page_key(controls: list[Any]) -> str:
    names = sorted(
        _label(control).casefold()
        for control in controls
        if isinstance(control, dict) and _label(control)
    )
    return "|".join(names)


def _unlabeled(controls: list[Any]) -> bool:
    named = [control for control in controls if isinstance(control, dict)]
    return bool(named) and all(not _label(control) for control in named)


def _packet(goal: str, controls: list[Any], actions: list[Any], picture: str | None) -> dict[str, Any]:
    page: dict[str, Any] = {"controls": controls}
    if picture:
        page["picture"] = picture
    if _unlabeled(controls):
        page["needs_picture"] = True
    return critic_packet(goal, [page], actions)


def follow_step(
    goal: str,
    step: dict[str, Any],
    controls: list[Any],
    actions: list[Any] | None = None,
    model: Any = None,
    failures: list[dict[str, Any]] | None = None,
    picture: str | None = None,
    step_index: int = 0,
) -> dict[str, Any]:
    """Press the saved button, or ask the model for one new button on this page."""
    if not isinstance(step, dict):
        raise ValueError("need the saved step")
    wanted = step.get("saved") or step.get("text") or ""
    if not isinstance(wanted, str):
        raise ValueError("need the button the task learned")
    decision = press_or_stop(wanted, controls, step.get("backups") or ())
    if decision["action"] == "press":
        decision["via"] = "saved"
        return decision
    trace = list(actions or [])
    trace.append({"step": step_index, "status": "missed", "cause": decision["reason"]})
    if _unlabeled(controls) and not picture:
        return {"action": "stop", "reason": "need a picture", "page": controls, "via": "saved"}
    packet = _packet(goal, controls, trace, picture)
    if model is None:
        return {**decision, "via": "saved", "packet": packet}
    answer = model(packet)
    if not isinstance(answer, str) or not answer.strip():
        return {"action": "stop", "reason": "the model gave no button", "page": controls, "packet": packet, "via": "model"}
    name = answer.strip()
    signature = page_key(controls)
    for failure in failures or []:
        if failure.get("page") == signature and str(failure.get("button", "")).casefold() == name.casefold():
            return {
                "action": "stop",
                "reason": "that button already failed on this page",
                "page": controls,
                "packet": packet,
                "via": "model",
            }
    pressed = press_or_stop(name, controls)
    if pressed["action"] != "press":
        return {
            "action": "stop",
            "reason": "the new button is not on the page",
            "page": controls,
            "packet": packet,
            "rejected": name,
            "via": "model",
        }
    pressed["via"] = "model"
    pressed["packet"] = packet
    return pressed


def note_hit(book: dict[str, Any] | None, step_index: int, controls: list[Any], button: str) -> tuple[dict[str, Any], str | None]:
    """Count this page for one new button. Two different pages admit it."""
    if isinstance(step_index, bool) or not isinstance(step_index, int) or step_index < 0:
        raise ValueError("need the broken step")
    fresh: dict[str, Any] = copy.deepcopy(book) if isinstance(book, dict) else {}
    slot = fresh.setdefault(str(step_index), {})
    if not isinstance(slot, dict):
        slot = {}
        fresh[str(step_index)] = slot
    pages = slot.setdefault(button, [])
    if not isinstance(pages, list):
        pages = []
        slot[button] = pages
    signature = page_key(controls)
    if signature and signature not in pages:
        pages.append(signature)
    return fresh, button if len([item for item in pages if isinstance(item, str)]) >= 2 else None


def _write_button(step: dict[str, Any], button: str) -> None:
    if "text" in step:
        step["text"] = button
    elif "saved" in step:
        step["saved"] = button
    else:
        args = step.get("args")
        if isinstance(args, dict) and isinstance(args.get("selector"), dict):
            args["selector"]["text"] = button
        else:
            step["text"] = button


def _job_text(after: Any) -> str:
    if after is None:
        return ""
    if isinstance(after, str):
        return after
    if isinstance(after, list):
        return " ".join(_label(item) for item in after if isinstance(item, dict))
    if isinstance(after, dict):
        return _job_text(after.get("text") or after.get("controls"))
    return ""


def job_happened(step: dict[str, Any], after: Any) -> bool | None:
    """None means this step has no result check."""
    check = step.get("check") if isinstance(step, dict) else None
    if not isinstance(check, str) or not check.strip():
        return None
    return check.strip().casefold() in _job_text(after).casefold()


def run_plan(
    goal: str,
    steps: list[dict[str, Any]],
    pages: list[Any],
    model: Any = None,
    book: dict[str, Any] | None = None,
    failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the saved steps. A miss may change only the broken step, and only after two pages."""
    if not isinstance(steps, list) or not isinstance(pages, list):
        raise ValueError("need the steps and the pages")
    fresh_steps = copy.deepcopy(steps)
    fresh_book = copy.deepcopy(book) if isinstance(book, dict) else {}
    seen_failures = list(failures or [])
    presses: list[str] = []
    actions: list[dict[str, Any]] = []
    asked = 0
    for index, step in enumerate(fresh_steps):
        if index >= len(pages):
            return {"status": "stopped", "reason": "the page ended", "presses": presses, "actions": actions, "steps": fresh_steps, "book": fresh_book, "failures": seen_failures, "asked": asked}
        page = pages[index]
        controls = page.get("controls") if isinstance(page, dict) else page
        picture = page.get("picture") if isinstance(page, dict) else None
        before = copy.deepcopy(fresh_steps)
        def counting_model(packet, inner=model):
            nonlocal asked
            asked += 1
            return inner(packet)
        decision = follow_step(goal, step, controls, actions, counting_model if model else None, seen_failures, picture, index)
        if decision["action"] != "press":
            if decision.get("rejected"):
                seen_failures.append({"page": page_key(controls), "button": decision["rejected"], "step": index})
            actions.append({"step": index, "status": "missed", "cause": decision.get("reason") or "this step missed"})
            return {
                "status": "stopped",
                "reason": decision.get("reason"),
                "presses": presses,
                "actions": actions,
                "steps": fresh_steps,
                "book": fresh_book,
                "failures": seen_failures,
                "packet": decision.get("packet"),
                "asked": asked,
            }
        presses.append(decision["control"]["id"])
        actions.append({"step": index, "status": "pressed"})
        after = page.get("after") if isinstance(page, dict) else None
        happened = job_happened(step, after)
        if happened is False:
            actions[-1] = {"step": index, "status": "missed", "cause": "the job did not happen"}
            if decision.get("via") == "model":
                seen_failures.append({"page": page_key(controls), "button": decision.get("matched"), "step": index})
            return {
                "status": "stopped",
                "reason": "the job did not happen",
                "presses": presses,
                "actions": actions,
                "steps": fresh_steps,
                "book": fresh_book,
                "failures": seen_failures,
                "asked": asked,
            }
        if decision.get("via") == "model" and happened is True:
            fresh_book, admitted = note_hit(fresh_book, index, controls, decision["matched"])
            if admitted:
                _write_button(fresh_steps[index], admitted)
                for other, original in enumerate(before):
                    if other != index:
                        fresh_steps[other] = original
    return {"status": "done", "presses": presses, "actions": actions, "steps": fresh_steps, "book": fresh_book, "failures": seen_failures, "asked": asked}


def revise_step(spec: dict[str, Any], step_index: int, button: str) -> dict[str, Any]:
    """Copy the plan and change the button name on one step."""
    if not isinstance(spec, dict):
        raise ValueError("need the saved task")
    if isinstance(step_index, bool) or not isinstance(step_index, int) or step_index < 0:
        raise ValueError("need the broken step")
    if not isinstance(button, str) or not button.strip():
        raise ValueError("need the button name to write")
    fresh = copy.deepcopy(spec)
    try:
        steps = fresh["plan"]["steps"]
    except (KeyError, TypeError) as error:
        raise ValueError("saved task has no steps") from error
    if not isinstance(steps, list) or step_index >= len(steps):
        raise ValueError("broken step is outside the plan")
    step = steps[step_index]
    if not isinstance(step, dict):
        raise ValueError("broken step is not a step")
    args = step.get("args")
    if not isinstance(args, dict):
        args = {}
        step["args"] = args
    selector = args.get("selector")
    if not isinstance(selector, dict):
        selector = {}
        args["selector"] = selector
    selector["text"] = button.strip()
    return fresh
