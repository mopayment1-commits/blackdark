"""HaasScript-style sandbox — restricted AST evaluator (no eval/exec)."""

from __future__ import annotations

import ast
import logging
import math
import operator
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

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
}

_CMP_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}


def _validate_tree(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _SAFE_FUNCS:
                raise ValueError(f"Disallowed call: {getattr(node.func, 'id', '?')}")
        elif not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f"Disallowed syntax: {type(node).__name__}")


def _eval_node(node: ast.AST, env: dict[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, env)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in env:
            raise ValueError(f"Unknown name: {node.id}")
        return env[node.id]
    if isinstance(node, ast.UnaryOp):
        op = _UNARY_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Disallowed unary op: {type(node.op).__name__}")
        return op(_eval_node(node.operand, env))
    if isinstance(node, ast.BinOp):
        op = _BIN_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Disallowed binary op: {type(node.op).__name__}")
        return op(_eval_node(node.left, env), _eval_node(node.right, env))
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            value: Any = True
            for elt in node.values:
                value = _eval_node(elt, env)
                if not value:
                    return value
            return value
        if isinstance(node.op, ast.Or):
            value = False
            for elt in node.values:
                value = _eval_node(elt, env)
                if value:
                    return value
            return value
        raise ValueError(f"Disallowed bool op: {type(node.op).__name__}")
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, env)
        for op_node, comparator in zip(node.ops, node.comparators, strict=True):
            op = _CMP_OPS.get(type(op_node))
            if op is None:
                raise ValueError(f"Disallowed compare op: {type(op_node).__name__}")
            right = _eval_node(comparator, env)
            if not op(left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.IfExp):
        return _eval_node(node.body, env) if _eval_node(node.test, env) else _eval_node(node.orelse, env)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _SAFE_FUNCS:
            raise ValueError("Disallowed call")
        if node.keywords:
            raise ValueError("Keyword arguments are not allowed")
        args = [_eval_node(arg, env) for arg in node.args]
        return _SAFE_FUNCS[node.func.id](*args)
    raise ValueError(f"Disallowed syntax: {type(node).__name__}")


def run_script(expression: str, *, variables: dict[str, float] | None = None) -> dict[str, Any]:
    """Evaluate safe numeric expression — no imports/attribute access/eval."""
    tree = ast.parse(expression, mode="eval")
    _validate_tree(tree)
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
        **_SAFE_FUNCS,
    }
    result = _eval_node(tree, safe_vars)
    signal = None
    if isinstance(result, bool):
        signal = "buy" if result else "hold"
    elif isinstance(result, (int, float)) and result != 0:
        signal = "buy" if result > 0 else "sell"
    return {
        "expression": expression,
        "result": result,
        "signal": signal,
        "variables": {k: v for k, v in safe_vars.items() if k not in _SAFE_FUNCS},
        "allowed_functions": list(_SAFE_FUNCS.keys()),
    }
