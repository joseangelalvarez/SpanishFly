# AGENTS.md

## Purpose
Instructions for coding agents working in SpanishFly. Keep changes minimal, aligned with existing architecture, and validated with runnable checks.

## Start Here
- Read [ENVIRONMENTS.md](ENVIRONMENTS.md) for virtual environment policy.
- Read [Persona/README.md](Persona/README.md) for Persona architecture and runtime constraints.
- Read [.github/skills/spanishfly-persona-module/SKILL.md](.github/skills/spanishfly-persona-module/SKILL.md) when the task is end-to-end Persona design or refactor.

## Workspace Conventions
- Environment isolation is mandatory per module:
  - Root dependencies belong in [requirements.txt](requirements.txt).
  - Persona dependencies belong in [Persona/requirements.txt](Persona/requirements.txt).
- Prefer local-model paths from [Persona/config_persona.json](Persona/config_persona.json). Do not introduce remote model loading as a default path.
- Preserve layered boundaries in [Persona/src/persona](Persona/src/persona):
  - `ui/` handles widgets, dialogs, signals/slots, and view state.
  - `workers/` executes long-running jobs and emits signals only.
  - `core/` contains generation and business logic.
  - `infra/` contains runtime checks, pathing, and validation.

## Run and Verify
From [Persona](Persona):
- Run app: `python -m persona`
- Functional check: `python functional_test_persona.py`
- Diagnostics: `python diagnose.py`

## Persona UX Invariants (Module Activation + Cancel)
Apply these rules whenever implementing or reviewing Persona activation/cancel behavior:

1. Single active module only.
- Never allow two modules active at the same time.
- When entering Persona from the main app, the main menu must be disabled or hidden.
- When Persona becomes inactive (normal close or confirmed cancel), main menu becomes active again.

2. Cancel must stop any active operation.
- Persona cancel action must target all in-flight work for the module (generation worker/thread and dependent tasks).
- Cancellation must propagate to worker/service cancellation signals/events and must not leave zombie threads.

3. Confirmation before destructive cancel.
- If there is active work, ask user to confirm cancellation.
- While confirmation is pending, no new module action should start.
- If user confirms: cancel work, clean up resources, return focus to main menu.
- If user rejects: keep Persona active and keep the current operation state coherent.

4. Focus and state restoration.
- After confirmed cancel, return UI focus to main menu entry point.
- Re-enable main menu controls only after Persona is fully inactive.

5. No hidden parallel flows.
- Starting Persona while another module is active must be blocked.
- Starting another module while Persona is active or cancelling must be blocked.

## Implementation Notes
- For Persona internals, review [Persona/src/persona/ui/main_window.py](Persona/src/persona/ui/main_window.py) and [Persona/src/persona/workers/generation_worker.py](Persona/src/persona/workers/generation_worker.py).
- For orchestrator behavior, review [launcher.py](launcher.py).
- Prefer explicit state transitions over implicit widget-side effects.

## PR/Change Checklist for This Area
- Main menu disabled/hidden when Persona opens.
- No second module can be launched while Persona is active.
- Cancel asks for confirmation if work is active.
- Confirmed cancel stops worker/service and returns to main menu focus.
- Main menu re-enabled only when module is fully inactive.
- Functional behavior verified with a reproducible run path.
