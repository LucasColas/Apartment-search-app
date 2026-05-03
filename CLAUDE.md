## Code Principles

### SOLID

Apply SOLID as guiding heuristics, not rigid ceremony:

- **SRP**: Keep modules/classes focused on a single responsibility. If a class mixes I/O, business logic, and formatting, split it.
- **OCP**: Prefer extension via composition and strategy objects/functions over editing core logic.
- **LSP**: Any subtype or Protocol implementation must satisfy the same pre/postconditions and return compatible semantics.
- **ISP**: Keep interfaces minimal: small Protocols, narrow signatures, pass callables when a full type is unnecessary.
- **DIP**: Depend on abstractions (Protocol/ABC) at module boundaries. Accept dependencies via constructor/function parameters; wire concrete implementations at entrypoints.

### Clean Code

- **Guard clauses**: Prefer early returns to reduce nesting. Handle error/edge cases at the top of a function and keep the happy path un-indented.
- **Function size**: If a function exceeds ~30 lines, it is likely doing too much — split it into smaller, well-named helpers.
- **No magic values**: Extract magic numbers and string literals into named constants or Enums. The name should convey intent, not just the value.
- **Boy Scout Rule**: When touching a file, leave it slightly cleaner than you found it — but keep improvements within the scope of the current task.

### OOP and Modeling

- Prefer object-oriented design when it improves clarity and encapsulation.
- Prefer composition over inheritance. Use inheritance only for true "is-a" relationships.
- Use Pydantic models to enforce typing and validation on data structures. Use dataclasses.

### DRY and Reuse

- Before implementing anything, always check what already exists in the codebase to avoid duplicating logic.
- If a piece of logic needs to be shared across modules, extract it into a dedicated reusable module.
- Always align with existing patterns and types when they exist.

### Clean Code Over Backward Compatibility

- Unless explicitly requested by the user, prefer a clean codebase over backward compatibility.
- When renaming or restructuring, update all references directly rather than introducing wrappers or aliases for compatibility.
- **Public API guardrail**: If changing a function/class/module that is imported by other packages, re-exported in __init__.py, referenced in docs, or used across multiple internal modules: search for usages first and update all call sites in the same change. If you cannot update all call sites, surface the risk and propose a safe alternative.

### TDD

Follow a strict red/green/refactor cycle:

1. **Red**: Write a failing test that defines the expected behavior.
2. **Green**: Write the MINIMAL implementation to make the test pass.
3. **Refactor**: Clean up while keeping tests green.

Always run the tests to verify your work before moving on.

---

## Conflict Resolution

When instructions or goals conflict, prioritize in this order:

1. **Correctness and safety** (tests passing, no regressions, invariants maintained)
2. **Performance** (especially for solver/model formulation and hot paths)
3. **Simplicity and maintainability** (clean design, minimal change set)
4. **Style preferences** (naming, formatting, OOP preference), as long as they preserve clarity

---

## Style and Conventions

### PEP 8

- Follow PEP 8 strictly.
- Use explicit, non-abbreviated names in the appropriate case format (e.g., snake_case for functions/variables, PascalCase for classes).

### Imports

- Use absolute imports exclusively.
- Place all imports at the top of the file.

### Typing

- Use concrete types or Self rather than from __future__ import annotations.
- Use native built-in types (list, dict, tuple, set, etc.) rather than their typing counterparts when available.
- Use Enum classes when a value is chosen from a small set of known options.

### Error Handling

- Only catch exceptions when you intend to handle them meaningfully. Let errors propagate naturally.

### Logging

- Use the standard `logging` module. Never use `print()` for operational output.
- One logger per module: `logger = logging.getLogger(__name__)`. Do not share or pass logger instances.
- Configure logging (level, format, handlers) once at the application entrypoint. Library/domain modules must never call `logging.basicConfig()` or attach handlers.
- Use levels intentionally: **DEBUG** for diagnostics, **INFO** for operational milestones, **WARNING** for recoverable surprises, **ERROR** for operation failures, **CRITICAL** for process-level failures.
- Pass variable data via `extra={}`, not f-strings, so log aggregators can parse fields.
- Use `logger.exception()` inside `except` blocks to capture the full traceback.
- Never log secrets, tokens, passwords, or personally identifiable information.


## Testing and Linting

### Running Tools (Mandatory)

Before making non-trivial changes, discover and record the exact commands used by this repo:

- Run tests: (fill in)
- Run linter: 
- Run formatter: black
- Run type checker: mypy

**Discovery order**: Makefile targets, pyproject.toml tool sections, tox.ini / noxfile.py, package.json scripts, README.md / CONTRIBUTING.md. Once discovered, update this section and use these exact commands for all subsequent work.

### Test Structure

- Mirror the source tree: one unit test file per module.
- Keep integration tests in a separate directory (tests/integration/) so they can be run independently.
- Place shared factories and fixtures in tests/conftest.py or a dedicated tests/factories.py to avoid duplicating setup logic across test files.

### Test Practices

- Use autospec over plain Mock whenever possible to catch interface mismatches.
- Prefer factories over patching to set up test data; this keeps tests decoupled from implementation details.
- Maintain meaningful coverage: cover edge cases and async paths. Update tests for any non-trivial change.
- All projects use SonarQube; check VSCode diagnostics to find and fix relevant issues.

---

## Documentation

- Once a feature or plan is done, update all related documentation accordingly (docstrings, READMEs, etc.).
- Every class and function should have a docstring unless it is completely trivial. Use a one-liner for short functions and a comprehensive docstring for complex ones.
- Keep comments inside docstrings; only add inline comments when they are truly necessary for clarity.

---

## Code Review

- Before flagging an issue, understand the full pipeline and data flow. Only alert on conditions that can actually occur given the upstream flow.
- Watch for edge cases, side effects, violations of this instruction file, and potential regressions in areas the code was not directly modified.

---

## Workflow

### Repo Scan Checklist

For non-trivial changes, do a minimal repo scan before coding:

- Identify entrypoints (CLI/app/web), main modules, and overall layering.
- Identify where core domain models live (e.g., Pydantic models) and follow existing patterns.
- Identify where tests live and how they are structured.
- Identify tooling configuration (formatter/linter/type checker/test runner).
- Identify existing patterns for errors/exceptions, logging, and configuration.

### Planning and Fixing

When making a plan or a fix, always summarize:

1. **Root cause**
2. **MINIMAL change set**
3. **Side effects and potential issues**

### Change Safety Checklist (Before Marking Done)

Before finalizing a change:

- Search for existing implementations to avoid duplication.
- Search for usages when renaming or changing behavior; update all call sites.
- Add/adjust tests for new behavior and edge cases.
- Run tests, linter, formatter, and type checker using the repo's recorded commands.
- Update docs/docstrings/READMEs that describe the modified behavior.

### Assumptions

- If requirements are ambiguous but you can proceed safely, proceed with best-effort defaults and explicitly list assumptions in your response.
- If ambiguity affects architecture, public APIs, or could cause data loss/regressions, ask before proceeding.

### Self-Improvement

- When the user flags a code convention issue, update this instruction file to prevent the same problem from recurring.