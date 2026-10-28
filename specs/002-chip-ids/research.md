# Research: chip ids on the start protocol line

## Decision 1: field 11, after the registration references

- **Decision**: the chip ids are field 11, written always by lines built in this program.
- **Rationale**: the constitution allows new data only after field 9; field 10 is taken by the
  site references. FinishProtocolGeneratorPython reads fields 0-9 (`StartProtocolElement.from_line`)
  and the site reads `fields[10]` once `line.count("#") >= 11` (`event_photos/bindings.py`), so a
  twelfth separator changes nothing for either; checked in their code on 2026-10-28.
- **Alternatives**: the comment field (rejected: constitution II keeps it for people); a separate
  file mapping chips to bibs (rejected: the maintainer wants the binding on the line, and a second
  file can drift from the protocol).

## Decision 2: the shape of a chip id

- **Decision**: one or more ASCII letters and digits, stored upper case; commas and semicolons
  separate ids; spaces and other ASCII characters inside an id are dropped.
- **Rationale**: readers report ids as hexadecimal EPCs (LLRP: Impinj, Zebra; cheap R2000 modules)
  or as alphanumeric transponder codes (RaceResult); upper case is how they print them, and the
  chronometers compare ids after the same normalisation. Labels print a 96-bit EPC in groups of four
  (`E280 1170 0000 020A`), and dashes and dots appear when people copy ids; none of them carries
  meaning. A space can also stand between two whole ids pasted without a comma, and no rule tells
  that from a grouped id: groups of four, of eight, a 32-character EPC in eight groups all occur.
  So a space never separates ids, and when cleaning drops anything inside an id the form shows the
  result and asks for Save again (review of the pull request, cycles 1 and 2).
- **Alternatives**: keeping ids exactly as typed (rejected: `e280...` and `E280...` would be two
  chips to a chronometer that compares strings).

## Decision 3: a character from another keyboard layout stops the save

- **Decision**: when a chip token contains a character outside ASCII, Save does nothing but say
  which ids are affected; the form keeps what was typed. Upper-casing and dropping ASCII
  punctuation happen silently.
- **Rationale**: a scanner that types as a keyboard while the Russian layout is on produces
  Cyrillic letters where the id has Latin ones; dropping them silently would save a different id
  and clear the form, and the rider would go untimed. Refusing once costs one retype at the desk.
- **Alternatives**: save and warn afterwards (rejected: the form is cleared by then and the wrong
  id is already in the protocol, possibly uploaded); transliterate look-alike letters (rejected:
  guessing; a wrong guess is worse than a refusal).
- **Spec impact**: FR-003, the edge case about a Cyrillic look-alike and User Story 1, scenario 2
  state this decision.

## Decision 4: chip problems have an indicator of their own that names the line

- **Decision**: a chip bound to two different bibs, a character outside ASCII in a written chip
  field and a relay rider with chips past the last stage light a second indicator next to the
  duplicate one, naming the first such line; the selection is not moved. `chip_rows()` finds both
  in one pass on every save.
- **Rationale**: a chip under two bibs makes every read of it ambiguous and the chronometers will
  refuse to guess, so the desk must see it. First planned as part of the duplicate indicator, which
  selects the repeated line; review (cycles 3 and 4) showed that a problem lasting until fixed
  would move the selection on every save and aim the next Delete at another rider.

## Decision 5: a relay's riders are separate groups

- **Decision**: semicolons separate the riders of a team in field 11, commas the ids of one rider.
  On a line with N > 1 stages and a numeric bib, the k-th rider binds to bib + k.
- **Rationale**: FinishProtocolGenerator expects stage riders as bibs number .. number + N - 1, and
  the site expands such a line the same way (`event_photos/bindings.py`), so a relay rider's chip
  read must become that rider's bib, not the team's first. Field 10 already lists one reference per
  member in member order; field 11 needs groups because a rider carries several chips.
- **Alternatives**: one flat list bound to the team's bib (rejected: stage 2 and 3 crossings would
  be credited to the stage 1 bib, found in review cycle 2); a field per stage (rejected: the number
  of stages varies per line).
