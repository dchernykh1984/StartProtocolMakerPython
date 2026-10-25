<!--
Sync Impact Report
- Version: none -> 1.0.0 (first constitution, with the registration-reference feature of
  cycling-site issue #349).
- Principles: I-V drawn from the code and its comments (app/models.py, app/main_window.py,
  app/http_io.py), VI-VII from CLAUDE.md / AGENTS.md and the skills under .claude/skills and
  .agents/skills, which stay the detailed runtime guidance. The scope note on unmaintained C++
  tools is the maintainer's decision of 2026-10-25.
- Templates: plan-template.md's "Constitution Check" gate reads these principles; no template
  needed changes.
-->

# Start Protocol Maker Constitution

Start Protocol Maker is the desk tool a race referee uses to turn registrations into a start
protocol: who starts, with which bib, in which group, with what start delay. It runs on the
referee's own computer at the start line, often without a reliable network, and hands its result
to the timing tools and to the cycling site.

## Core Principles

### I. Offline first

Everything the referee needs works without a network. The record is the plain text kept next to
the program -- the backup (`data/spm_backup.txt`) and the start protocol file -- not anything on
the site. The site is an exchange the referee may use: loading registrations, sending the start
list. A missing network delays an upload; it never blocks registration, an edit or a save.

### II. The start line is a shared contract

A start protocol line is `number#name#group#laps#stage#year_of_birth#team#city#comment#time_shift#`.
Other programs read it: FinishProtocolGeneratorPython, WindowsChronometerPython and the site, which
stores the uploaded lines. Fields 0-9 keep their position and meaning; the comment stays free text
for people and is never used to carry machine data. New data is added only as optional fields after
field 9, and only after checking that every maintained reader ignores what it does not know. The
unmaintained C++ tools are not a constraint (maintainer, 2026-10-25).

### III. Old files stay readable

A backup or start protocol written by an earlier version loads in a later one. New backup tags are
appended after the existing ones, because tags are read back in their order. A field a version
does not know is kept as it is, not dropped, wherever the line is not rebuilt from the form.

### IV. Known facts are not asked for again

What the site already sent -- names, groups, laps, bib ranges, the registration a line came from --
is kept with the line and reused, so nobody types it twice. A merge from the site recognises lines
it already has instead of adding them again.

### V. The referee's work is never lost

A failure is reported, not fatal: every network or response error becomes a message in the
interface, never an exception that closes the window. An automatic upload reports in a status
label and retries on a timer; only a button the referee just pressed may open a dialog. Every
change is saved to the backup before anything is sent.

### VI. Behaviour is proven by tests

A behaviour change ships with a test that fails without it. The window is excluded from coverage,
so a handler change needs a Qt-level test in `tests/test_window.py`; the 90% coverage gate covers
the rest. Tests use placeholder tokens, never a real competition's.

### VII. Plain, attributable history

Files are ASCII. Commits follow Conventional Commits in one line with no trailers, because
release-please builds the changelog from them. Work is published under the owner's name with no AI
credit anywhere. Every change goes through a pull request from a branch off `origin/main`.

## Constraints

- Python 3.14 and PySide6, run through `uv`; HTTP through the standard library with a 10 second
  timeout, no HTTP client dependency.
- Portable builds for Windows, macOS (Apple Silicon) and Linux; the program keeps its files next to
  itself, so one copy of the folder serves one event.

## Development Workflow

- A feature that changes a file format, the site exchange or what the referee sees gets a
  specification in `specs/<NNN>-<short-name>/` made with the Spec Kit skills (`/speckit-specify`,
  `/speckit-plan`, `/speckit-tasks`, `/speckit-implement`). The maintainer reviews the
  specification and the plan before implementation starts. A change driven by a cycling-site
  issue names that issue in its specification.
- `specs/app/` describes the program as it works today. A change that alters described behaviour
  updates it in the same pull request.
- A bug fix or a small change needs no specification of its own.

## Governance

This constitution states the principles; `CLAUDE.md`, `AGENTS.md` and the skills they list hold the
detail and are kept consistent with it. The maintainer amends it through a pull request that bumps
the version -- MAJOR for a principle removed or redefined, MINOR for one added or materially
expanded, PATCH for wording -- and updates the Last Amended date.

**Version**: 1.0.0 | **Ratified**: 2026-10-25 | **Last Amended**: 2026-10-25
