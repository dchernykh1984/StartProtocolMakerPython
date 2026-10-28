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

- **Decision**: one or more ASCII letters and digits, stored upper case; commas, semicolons and
  whitespace separate ids; other ASCII characters inside an id are dropped.
- **Rationale**: readers report ids as hexadecimal EPCs (LLRP: Impinj, Zebra; cheap R2000 modules)
  or as alphanumeric transponder codes (RaceResult); upper case is how they print them, and the
  chronometers compare ids after the same normalisation. Dashes and dots appear when people copy
  ids from labels and carry no meaning.
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
- **Spec impact**: FR-003 and the edge case about a Cyrillic look-alike say "saving tells the
  registrar"; the first review cycle aligns them with this decision.

## Decision 4: a duplicate chip lights the existing indicator

- **Decision**: `duplicate_chip_row()` feeds `_refresh_duplicate_indicator()` like
  `duplicate_ref_row()`.
- **Rationale**: one indicator, one place the registrar looks; a chip on two lines makes every
  read of it ambiguous and the chronometers will refuse to guess.
