"""Built-in tools offered to any model with the `tools` capability
(AIModel.can_use_tools). Deliberately small and side-effect-free — no
network access, no filesystem access — since this app has no auth and
anything a tool can do, any page on the user's LAN could indirectly trigger
by driving the chat UI.
"""

import ast
import datetime
import operator

from langchain_core.tools import BaseTool, tool

_SAFE_BIN_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_SAFE_UNARY_OPERATORS = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class UnsafeExpressionError(ValueError):
    pass


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_BIN_OPERATORS:
        return _SAFE_BIN_OPERATORS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_UNARY_OPERATORS:
        return _SAFE_UNARY_OPERATORS[type(node.op)](_safe_eval(node.operand))

    raise UnsafeExpressionError(f"Unsupported expression: {ast.dump(node)}")


def evaluate_arithmetic(expression: str) -> float:
    """Parses `expression` as a Python AST and walks it through an explicit
    operator allowlist — never calls `eval`/`compile` on the expression
    itself, so there's no path to arbitrary code execution regardless of
    what the model (or a prompt-injected document) puts in `expression`.
    """
    tree = ast.parse(expression, mode="eval")

    return _safe_eval(tree.body)


@tool
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression, e.g. "2 + 2 * (3 - 1)".
    Supports +, -, *, /, //, %, ** and parentheses only — no variables,
    function calls, or names of any kind.
    """
    try:
        result = evaluate_arithmetic(expression)
    except (UnsafeExpressionError, SyntaxError, ZeroDivisionError, TypeError) as e:
        return f"Error: could not evaluate {expression!r}: {e}"

    return str(result)


@tool
def current_datetime() -> str:
    """Get the current date and time in UTC."""
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


BUILTIN_TOOLS: list[BaseTool] = [calculator, current_datetime]
BUILTIN_TOOLS_BY_NAME: dict[str, BaseTool] = {t.name: t for t in BUILTIN_TOOLS}
