# Working in this repository

Start Protocol Maker is a PySide6 desktop app that race referees use to build start
protocols offline and push them to the cycling site. Its sibling repository,
WindowsChronometerPython, records finish and group-start times against the same site
API; the two share conventions, so most of what follows applies there as well.

## Conventions

- Python 3.14. Everything runs through `uv`: `uv run pytest`, `uv run ruff check .`,
  `uv run mypy app tests`.
- Never commit to `main`. Branch off `origin/main`, one logical change per commit.
- Commit messages: Conventional Commits, a single line, no trailers and no co-author
  line. `cz check --rev-range origin/main..HEAD` runs on every PR, and release-please
  builds `CHANGELOG.md` from these messages, so the type matters (`fix:` and `feat:`
  are released, `chore:`/`docs:`/`test:`/`style:` are not).
- ASCII only in source, config and docs. A pre-commit hook rejects anything else
  (`uv.lock` and `CHANGELOG.md` are exempt). Discussion happens in whatever language
  the user writes in; files stay ASCII.
- `uv run` may rewrite `uv.lock`, because main's lock is out of step with
  `pyproject.toml`. Keep that out of feature commits with `git checkout uv.lock`
  unless the lock itself is the change.
- Before committing: `uv run pytest` (the coverage gate is 90%), `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy app tests`. pre-commit runs the same
  set again on commit.

## What the tests actually cover

`app/main.py` and `app/main_window.py` are excluded from coverage
(`pyproject.toml`, `[tool.coverage.run]`), so the coverage number says nothing about
the window. Handler behaviour is protected only by the Qt-level tests in
`tests/test_window.py`. A change to a handler needs a test there, or it is unguarded.

## Skills

- `ship-a-change` -- branch, commit, open the PR with `gh`, watch CI to green.
- `review-cycle` -- review a branch or PR and land the fixes.
- `qt-window-tests` -- how to test PySide6 windows here.
- `cycling-site-api` -- how both apps talk to the cycling site.
