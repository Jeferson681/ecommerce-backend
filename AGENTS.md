# AGENTS.md

## Purpose

This file defines the operational rules for agents working in this repository.

The goal is to preserve scope, architecture, code quality, and the project's
continuity during the final stretch of development and preparation for
portfolio delivery.

## Before changing code

1. Read the `README.md`.
2. Consult the relevant technical documentation in `docs/`.
3. Verify the existing structure before creating new files or abstractions.
4. Identify the modules, flows, contracts, and tests affected.
5. Consult `docs/private_docs/` when the work depends on internal decisions or analyses.
6. Check the current Git state before starting (`git status -sb`), including
   files already staged. Staged files that are not part of the task must be
   left untouched.

Do not implement a solution before understanding where the responsibility already exists.

## Scope

### Main rule

Make only the changes necessary for the current task.

Do not turn a fix into an opportunity to:

- refactor unrelated code;
- reorganize directories without need;
- replace existing patterns without reason;
- add functionality outside the scope;
- fix unrelated problems found incidentally.

If you find an unrelated problem, do not fix it. Record it in the delivery
report as a finding, with file and line, so it can be handled in its own task.

If an additional change is required to keep the solution consistent, justify it.

## Architecture

- Preserve the existing responsibilities of the modules.
- Reuse existing components before creating new ones.
- Do not introduce abstractions merely to reduce a few lines of code.
- Do not change public contracts without justification.
- Do not change the architecture merely out of personal preference.
- When a relevant architectural decision changes, update the corresponding documentation.

## Implementation

Implement incrementally.

Preference:

1. smallest necessary change;
2. validation;
3. next necessary change;
4. validation again.

Avoid broad changes when a localized change solves the problem.

## Tests

Every behavioral change must have proper validation.

Prioritize:

- unit tests for isolated behavior;
- integration tests when there is real interaction between components;
- regression tests when there is a bug fix;
- smoke tests when the change affects the integrated behavior of the application.

A regression test must represent the behavior that previously failed.

Do not consider a test valid merely because it runs without errors. When applicable, confirm that the test would actually detect the regression without the fix.

Run tests with `pytest -q -p no:cacheprovider` to avoid creating cache files in the repository.
Integration tests (`-m integration`) require PostgreSQL and the Alembic migrations applied.

## Verification commands

Prefer the targets in the `Makefile` when they exist. Otherwise use:

- Lint: `ruff check .`
- Types: `mypy backend/app`
- Unit tests: `pytest -q -p no:cacheprovider -m "not integration"`
- Integration tests: `pytest -q -p no:cacheprovider -m integration`
- Hooks, all files: `pre-commit run --all-files`
- Documentation-only changes: `git diff --check`

Do not invent commands. If a command is not listed here or in the `Makefile`, check the CI workflows in `.github/workflows/` before using it.

## CI

The repository has separate workflows for distinct responsibilities.

Do not create a new workflow just to consolidate existing ones.

Before changing CI:

- audit the existing workflow;
- confirm the gap;
- change only what is necessary;
- preserve the separation between unit tests, integration, lint, smoke test, and builds as long as it remains justifiable.

## Git

### Before finishing

```bash
git status
git diff
git diff --cached
```

Verify that:

- all changes belong to the task;
- there are no unexpected files;
- there are no accidental changes;
- temporary files will not be included;
- no unrelated file is staged.

### Commits

- Commits must represent a logical unit of work.
- Write commit messages in English, using conventional prefixes:
  `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `ci:`, `perf:`, `chore:`.
- The message should explain the reason for the change when it is not evident from the title.
- Do not add `Co-authored-by` or any other AI attribution trailer unless the user explicitly asks for it.
- Do not commit credentials, tokens, `.env`, temporary files, databases, caches, or runtime artifacts.
- When other files are staged, commit with an explicit pathspec, for example
  `git commit -m "docs(env): ..." -- .env.example`, so that unrelated staged files are not included.
- Never use `git add -A` or `git add .`. Add files by name.

### Hooks

- Do not bypass hooks with `--no-verify` or by disabling them.
- If a hook fails, stop, report the output, and fix the cause. Do not work around it.
- If the hook cannot run because of the local environment, report it. Do not change the hook configuration to make it pass.

### Remote operations

- Do not push, force-push, rebase, or amend commits that may already exist on the remote without explicit approval from the user.
- Before any history rewrite, confirm that the commits are local-only (`git rev-list @{u}..HEAD` or equivalent).

## Documentation

Update documentation only when the change actually modifies:

- behavior;
- contract;
- architecture;
- execution;
- configuration;
- relevant process.

When environment variables change, update `.env.example` with placeholders or
the defaults defined in the code, and never with real values.

Do not create redundant documentation.

Planning, analysis, audit, and personal tracking documents must remain in `docs/private_docs/`.

## Security

- Do not log, print, or commit secrets, tokens, or passwords, including in test output.
- JWT validation must keep signature, issuer, audience, and expiration checks.
- Stripe webhooks must verify the signature before any processing.
- Refresh tokens are stored hashed. Do not store or return the raw token value.
- Do not enable `DEBUG` behavior in production configuration.
- When in doubt about a security change, report it instead of changing it.

## Task completion

A task is only complete when:

- the required implementation is done;
- the relevant tests have been run;
- the relevant lint has been run;
- the relevant CI has been considered;
- the diff has been reviewed;
- there are no unrelated changes;
- the necessary documentation has been updated;
- the Git state has been verified and reported, including staged files.

Do not declare the task complete merely because the code was changed or because an isolated test passed.

## Final delivery stretch

During the final stretch of the project, the priority is:

1. fixing real problems;
2. preserving scope;
3. validating behavior;
4. avoiding unnecessary refactoring;
5. keeping documentation coherent;
6. ensuring the project is presentable for the portfolio.

Do not add process or architectural complexity without concrete benefit for the delivery.
