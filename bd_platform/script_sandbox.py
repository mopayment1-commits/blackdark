"""HaasScript-style sandbox — restricted expression evaluator."""

from __future__ import annotations

import ast
import logging
import math
from typing import Any

logger = logging.getLogger("BLACKDARK.ScriptSandbox")

_ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.BoolOp,
    ast.IfExp,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Call,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.Pow,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.And,
    ast.Or,
    ast.Not,
    ast.USub,
    ast.UAdd,
)

_SAFE_FUNCS = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "sqrt": math.sqrt,
}


def _validate_script_node(node: ast.AST) -> None:
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _SAFE_FUNCS:
            raise ValueError(f"Disallowed call: {getattr(node.func, 'id', '?')}")
        return
    if not isinstance(node, _ALLOWED_NODES):
        raise ValueError(f"Disallowed syntax: {type(node).__name__}")


def _signal_from_result(result: Any) -> str | None:
    if isinstance(result, bool):
        return "buy" if result else "hold"
    if isinstance(result, (int, float)) and result != 0:
        return "buy" if result > 0 else "sell"
    return None


def run_script(expression: str, *, variables: dict[str, float] | None = None) -> dict[str, Any]:
    """Evaluate safe numeric expression — no imports/attribute access."""
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        _validate_script_node(node)
    safe_vars = {
        "price": 0.0,
        "rsi": 50.0,
        "volume": 0.0,
        "funding": 0.0,
        "obi": 0.0,
        "sentiment": 0.0,
        "ma_fast": 0.0,
        "ma_slow": 0.0,
        **(variables or {}),
    }
    result = eval(
        compile(tree, "<strategy>", "eval"),
        {"__builtins__": {}},
        {**_SAFE_FUNCS, **safe_vars},
    )
    return {
        "expression": expression,
        "result": result,
        "signal": _signal_from_result(result),
        "variables": safe_vars,
        "allowed_functions": list(_SAFE_FUNCS.keys()),
    }
