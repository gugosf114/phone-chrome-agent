"""Small, explicit skill contract. Templates are data, never evaluated code."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

from .models import Step, TaskPlan, validate_secret_storage

NAME = re.compile(r"[a-z][a-z0-9_-]{0,79}\Z")
SLOT = re.compile(r"\{\{([a-zA-Z][a-zA-Z0-9_]*)\}\}")
TYPES = {"string": str, "integer": int, "number": (int, float),
         "boolean": bool, "array": list, "object": dict}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def bind(value: Any, inputs: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        if "$input" in value:
            if set(value) != {"$input"} or value["$input"] not in inputs:
                raise ValueError("invalid or undeclared $input")
            return copy.deepcopy(inputs[value["$input"]])
        return {key: bind(child, inputs) for key, child in value.items()}
    if isinstance(value, list):
        return [bind(child, inputs) for child in value]
    if isinstance(value, str):
        def replace(match):
            key = match.group(1)
            if key not in inputs:
                raise ValueError(f"undeclared input {key!r}")
            if not isinstance(inputs[key], (str, int, float, bool)):
                raise ValueError("structured inputs need a {$input: name} reference")
            return str(inputs[key])
        return SLOT.sub(replace, value)
    return value


def validate_inputs(spec: dict, supplied: dict) -> dict:
    if not isinstance(supplied, dict):
        raise ValueError("inputs must be an object")
    declarations = spec["inputs"]
    if set(supplied) - set(declarations):
        raise ValueError("unknown input parameter")
    result = copy.deepcopy(supplied)
    for name, rule in declarations.items():
        if name not in result:
            if "default" not in rule:
                raise ValueError(f"missing input {name!r}")
            result[name] = copy.deepcopy(rule["default"])
        value = result[name]
        if not isinstance(value, TYPES[rule["type"]]) or (
            rule["type"] in {"integer", "number"} and isinstance(value, bool)
        ):
            raise ValueError(f"input {name!r} must be {rule['type']}")
        if "enum" in rule and value not in rule["enum"]:
            raise ValueError(f"input {name!r} is outside its enum")
    validate_secret_storage(result, ())
    canonical(result)
    return result


def validate_spec(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("skill must be an object")
    spec = json.loads(canonical(raw))
    if not NAME.fullmatch(str(spec.get("id", ""))):
        raise ValueError("skill id must be lowercase letters, digits, hyphens or underscores")
    if not isinstance(spec.get("description"), str) or not spec["description"].strip():
        raise ValueError("skill needs a description")
    if not isinstance(spec.get("inputs"), dict):
        raise ValueError("skill inputs must be an object of type declarations")
    if not isinstance(spec.get("tags", []), list) or not all(isinstance(x, str) for x in spec.get("tags", [])):
        raise ValueError("tags must be strings")
    for name, rule in spec["inputs"].items():
        if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]*", name):
            raise ValueError("invalid input name")
        if not isinstance(rule, dict) or rule.get("type") not in TYPES:
            raise ValueError(f"input {name!r} needs a supported type")
        if set(rule) - {"type", "description", "default", "enum"}:
            raise ValueError(f"unsupported input rule for {name!r}")
        if "enum" in rule and (not isinstance(rule["enum"], list) or not rule["enum"]):
            raise ValueError("enum must be a non-empty list")
    plan = spec.get("plan")
    if not isinstance(plan, dict) or not isinstance(plan.get("task"), dict):
        raise ValueError("skill needs plan.task and plan.steps")
    if not isinstance(plan["task"].get("goal"), str) or not plan["task"]["goal"].strip():
        raise ValueError("skill plan needs a non-empty goal")
    if set(plan["task"]) - {"goal", "browser_backend"}:
        raise ValueError("skill task accepts only goal and browser_backend; runtime owns task identity")
    if not isinstance(plan.get("steps"), list) or not 1 <= len(plan["steps"]) <= 100:
        raise ValueError("skill needs 1 to 100 steps")
    for step in plan["steps"]:
        Step.from_dict(step)
    outputs = spec.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        raise ValueError("skill needs output paths into observed step results")
    for name, path in outputs.items():
        if not isinstance(name, str) or not isinstance(path, str) or not re.fullmatch(r"[0-9]+\..+", path):
            raise ValueError("outputs use paths such as 0.payload.title")
        if int(path.split(".")[0]) >= len(plan["steps"]):
            raise ValueError("output references a missing step")
    def references(value):
        if isinstance(value, dict):
            if "$input" in value:
                if set(value) != {"$input"} or not isinstance(value["$input"], str) or value["$input"] not in spec["inputs"]:
                    raise ValueError("undeclared or invalid $input")
            for child in value.values():
                references(child)
        elif isinstance(value, list):
            for child in value:
                references(child)
        elif isinstance(value, str):
            for name in SLOT.findall(value):
                if name not in spec["inputs"]:
                    raise ValueError(f"undeclared input {name!r}")
    references(plan)
    validate_secret_storage(spec, ())
    return spec


def instantiate(spec: dict, inputs: dict, task_id: str) -> TaskPlan:
    raw = bind(spec["plan"], validate_inputs(spec, inputs))
    raw["task"]["id"] = task_id
    raw["task"]["permission"] = {
        "authority": "full", "scope": "task", "targets": ["*"],
    }
    return TaskPlan.from_dict(raw, task_id)


def validate_outcome(expect: dict) -> None:
    if not isinstance(expect, dict) or not expect or set(expect) - {"equals", "contains"}:
        raise ValueError("evaluation needs equals/contains outcome expectations")
    meaningful = False
    for operator, checks in expect.items():
        if not isinstance(checks, dict):
            raise ValueError("outcome expectations must be field maps")
        for field, wanted in checks.items():
            if not isinstance(field, str) or not field:
                raise ValueError("outcome field is empty")
            if operator == "contains" and wanted in ("", None):
                raise ValueError("outcome contains value cannot be empty")
            meaningful = True
    if not meaningful:
        raise ValueError("evaluation needs a non-empty outcome expectation")
