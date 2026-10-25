# Feature Specification: Keep the site registration on every start protocol line

**Feature Branch**: `docs/registration-references`

**Created**: 2026-10-25

**Status**: Draft for maintainer review; no application change in this pull request

**Input**: cycling-site issue [#349](https://github.com/dchernykh1984/cycling-site/issues/349)
(event photos found by bib). The site needs to know which registration received which bib, and
that link is lost when registrations are loaded into Start Protocol Maker. The site side is in
the [issued bib exchange contract](https://github.com/dchernykh1984/cycling-site/blob/349-external-photo-albums/specs/349-external-photo-albums/contracts/start-list-bindings.md).

**Decision (maintainer, 2026-10-25)**: variant A of the site contract -- a trailing field on the
line, shown as an ordinary field of the form. FinishProtocolGenerator and the chronometers stay
unchanged and ignore it; the site reads it from the start-list upload.

## User Scenarios & Testing

### User Story 1 - A loaded registration keeps its link through numbering (Priority: P1)

The referee loads registrations from the site. Registration on the spot is: open a
pre-registration line in the form, give it a bib with Get number and AutoShift, fix a typo, save
it to the protocol list. Each protocol line still says which site registration it came from, in
the same text line, with nothing else to keep beside it: the field is on both lists.

**Why this priority**: Without it the site cannot show a rider their own photos or results without
asking for the bib again, and guessing by name is not acceptable.

**Independent Test**: Load two registrations, number them, edit one in the form, save, restart the
program and send the start list; both uploaded lines carry their registration references.

**Acceptance Scenarios**:

1. **Given** a registration with `id` 1234 loaded from the site, **When** the referee opens it in
   the form and saves it with a bib, **Then** the protocol line ends in `#r1234#`.
2. **Given** a protocol line with a reference, **When** the referee changes its bib, name, group or
   delay in the form and saves, **Then** the reference is unchanged.
3. **Given** a line copied verbatim to the protocol ("open to protocol"), **Then** its reference is
   copied with it.
4. **Given** a backup with references, **When** the program restarts, **Then** every line has them.

### User Story 2 - A team keeps every member's link (Priority: P1)

The referee builds a relay team in the form from separate registrations with "Add into team".

**Why this priority**: A relay shares one line and one bib; without every member's reference only
one of them, or none, would be linked.

**Independent Test**: Add two registrations into one team and save; the line carries both
references in member order.

**Acceptance Scenarios**:

1. **Given** registrations 2101 and 2117 added into one team, **Then** the line ends in
   `#r2101,r2117#`.
2. **Given** a relay registered on the site as one team entry (members joined by `<BR>`), **Then**
   its line carries the one reference of that entry.

### User Story 3 - The referee sees and controls the link (Priority: P2)

The reference is a visible field of the form, next to team and city -- not hidden state. The
referee sees which site registration the line belongs to and can clear the field when the form is
reused for a different person.

**Why this priority**: The form is reused all day; a link carried onto the wrong person would give
one rider another rider's photos.

**Independent Test**: Open a linked line, clear the field, save; the new line has no reference. Clear the
form and type a new entrant; the line has no reference.

**Acceptance Scenarios**:

1. **Given** a line opened from the open list, **Then** the form's reference field shows its
   tokens, for example `r1234`.
2. **Given** the referee clears that field, **Then** the saved line has an empty reference field.
3. **Given** an emptied form and a hand-typed on-the-day entrant, **Then** the saved line has no
   reference; nothing is inferred from the name.

### User Story 4 - Merges and checks use the link (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a registration renamed on the site after it was loaded, **When** the referee merges
   from the site again, **Then** the existing open-list line is recognised by its reference and no
   second line is added.
2. **Given** one reference on two protocol lines, **Then** the duplicate indicator reports it like
   a repeated bib.

### User Story 5 - Nothing else changes for other programs (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a start protocol file with references, **When** the current FinishProtocolGenerator
   reads it, **Then** its protocol is identical to the one made from the same file without them.
2. **Given** a backup written by 0.4.0, **Then** it loads, and its lines work without references.
3. **Given** a line with a reference token kind this version does not know, or more fields after
   it, **Then** the line is kept as it is unless the referee rebuilds it from the form, and an
   unknown token is carried over unchanged when it is.

### Edge Cases

- The same person entered twice for two distances: two registrations, two lines, two references.
- `NOT_PAID` in field 0 of an open-list line: the reference is kept; the bib is given at the start.
- Replace from site clears the open list; protocol lines keep their references.
- A registration deleted on the site after loading: the line keeps the reference; the site ignores
  references it does not recognise. Start Protocol Maker does not check them.
- A line typed into the backup by hand with spaces in the field: tokens are trimmed on load.

## Requirements

### Functional Requirements

- **FR-001**: Add one optional field after the start delay (index 10): empty, or comma-separated
  tokens. Version 1 defines `r<registration id>` (decimal). No spaces, `#` or line breaks.
- **FR-002**: Loading from the site writes `r<id>` from each participant's `id` into the line.
- **FR-003**: The form has a visible, editable reference field. Opening a line from either list
  fills it; Save writes it into the new line. Clearing the form empties it; the referee may also
  clear or type it by hand (the site ignores a token it does not recognise for the event).
- **FR-004**: "Add into team" appends the added registration's tokens to the form's tokens, in
  member order, without duplicates.
- **FR-005**: Every path that copies a line verbatim keeps the field, and anything after it.
- **FR-006**: Merge from site matches by reference first, then by the current
  `(last name, first name, year)` key.
- **FR-007**: The duplicate indicator also reports a reference used on two protocol lines.
- **FR-008**: The start list upload, the start protocol file, FTP push and the backup carry the
  lines as they are; no new request field, file or backup tag.
- **FR-009**: Fields 0-9 keep their position and meaning; the comment is not used for references.

### Key Entities

- **Entry reference**: a token naming one site registration of the event whose token delivered
  it. It is not an account ID: one account may file several entries, and in free registration the
  account is the submitter, not the athlete.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A round trip -- load, number, edit, assemble a team, save, restart, upload -- ends
  with every loaded line carrying its references, proven by Qt-level tests.
- **SC-002**: FinishProtocolGeneratorPython produces the same protocol from files with and without
  references (a fixture compared in tests).
- **SC-003**: Every backup fixture written by 0.4.0 still loads.

## Assumptions

- The site reads references from uploaded lines (cycling-site contract, variant A); until it does,
  the field is carried and ignored. FinishProtocolGenerator and the chronometers are not changed.
- Unmaintained C++ tools are not considered (maintainer, 2026-10-25).
- An older Start Protocol Maker keeps loaded lines but drops the field when it rebuilds a line from
  its form; the site contract says how it treats that loss.
