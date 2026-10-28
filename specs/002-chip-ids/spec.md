# Feature Specification: Keep each rider's timing chips on the start protocol line

**Feature Branch**: `feat/chip-ids`

**Created**: 2026-10-28

**Status**: Implemented in this pull request

**Input**: ChronometerPython issue
[#49](https://github.com/dchernykh1984/ChronometerPython/issues/49), comments 7 and 8. Maintainer's
decision of 2026-10-28: the registration program owns the binding between a bib and its timing
chips. Each start protocol line gets one more field with the rider's chip ids, in the
pre-registration list, in on-the-spot registration and as an editable form field. The site does not
send chips yet, so a line from the site arrives with the field empty. Later, chips will live in the
rider's site account: a rider only says "I take part", checks in by passing the antennas at the start
corral and is timed by chips from then on, with no registration on the spot.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The registrar records a rider's chips with the bib (Priority: P1)

At the registration desk the registrar opens a line, gives it a bib and types or scans the rider's
chip ids into the form's chip field: one chip, two (fork and seat post) or more. Saving puts them
into the start protocol line. The chronometer later reads them from the start protocol file, or
from the copy uploaded to the site, and knows whose crossing a chip read is.

**Why this priority**: Without the binding no chip read can become a crossing; it is the input
every chip timing feature depends on.

**Independent Test**: Open a line, enter `e280 1170 0000 020a, E2801170000002AB`, save, restart the
program; the protocol line, the start protocol file and the uploaded start list all end in
`#E28011700000020A,E2801170000002AB#`.

**Acceptance Scenarios**:

1. **Given** a line opened in the form, **When** the registrar enters two chip ids and saves, **Then**
   the protocol line carries both in field 11, upper case, comma-separated, in the order typed.
2. **Given** a chip id with a Cyrillic letter in it, **When** the registrar saves, **Then** nothing
   is saved, the message names that id, and the form still holds everything typed.
3. **Given** a protocol line with chips, **When** the registrar changes its bib, name, group or
   delay in the form and saves, **Then** the chips are unchanged.
4. **Given** a line copied verbatim to the protocol ("open to protocol"), **Then** its chips are
   copied with it.
5. **Given** a backup with chips, **When** the program restarts, **Then** every line has them.
6. **Given** a saved line, **Then** the form's chip field is empty for the next rider, as the
   reference field is.

---

### User Story 2 - Lines from the site keep the local chips (Priority: P1)

The registrar loads registrations from the site before the event and again on the day. The site
sends no chips yet, so its lines arrive with an empty chip field; chips typed at the desk must
survive every later merge.

**Why this priority**: A merge that wiped the chips typed at the desk would silently take riders out
of chip timing.

**Independent Test**: Load registrations, add chips to one open-list line, merge from the site
again; the line keeps its chips and no duplicate line is added.

**Acceptance Scenarios**:

1. **Given** a registration loaded from the site, **Then** its line has field 11, empty.
2. **Given** an open-list line with chips and a site reference, **When** the registrar merges from
   the site again, **Then** the line keeps its chips.
3. **Given** an old open-list line without a reference that a merge links to a registration,
   **Then** it keeps its chips while it takes the reference.

---

### User Story 3 - A team and a duplicate chip (Priority: P2)

A relay shares one bib: the registrar adds members into a team, and each member's chips belong to
that bib. A chip handed out twice is a mistake the registrar must see before the start.

**Why this priority**: A chip on two lines makes a read ambiguous; the chronometer will refuse to
guess, so the rider would go untimed. The registration desk is the place to catch it.

**Independent Test**: Join two members with chips into a team and save; the line carries the chips
of both, one rider after the other. Put one chip under two different bibs; the chip indicator
names the line.

**Acceptance Scenarios**:

1. **Given** two members with chips joined by "Add into team", **Then** the team's line carries
   each member's chips as a rider of its own, after a semicolon, in member order, without repeats.
2. **Given** one chip bound to two different bibs, **Then** the chip indicator names the second
   line, and the selection stays where the registrar put it.
3. **Given** a relay of three stages with bib 21, **Then** its second rider's chips bind to bib 22.

---

### User Story 4 - Nothing else changes for other programs (Priority: P1)

**Why this priority**: The start protocol line is a contract read by other programs (constitution,
principle II).

**Acceptance Scenarios**:

1. **Given** a start protocol file with chips, **When** FinishProtocolGeneratorPython reads it,
   **Then** its protocol is identical to the one made from the same file without chips (it reads
   fields 0-9).
2. **Given** an uploaded start list with chips, **Then** the site still reads the registration
   reference from field 10 (it reads `fields[10]` by index once a line has 11 separators).
3. **Given** a backup or a start protocol written by 0.5.x (11 separators, no chip field), **Then**
   it loads and its lines work without chips.
4. **Given** a line with more fields after the chip field, **Then** the line is kept as it is unless
   the registrar rebuilds it from the form.

### Edge Cases

- Chip ids typed with spaces inside (`E280 1170 0000 020A`, as labels print them): one id, shown
  joined before it is saved. Two whole ids pasted with a space instead of a comma are shown joined
  too, and the registrar adds the comma.
- Lower case and stray punctuation (`e2801170-0000-020a`): ids are case-insensitive and kept upper
  case; any character other than an ASCII letter or digit inside an id is dropped.
- A Cyrillic letter that looks Latin (the keyboard layout was Russian, or a desk reader typed into
  it): it is not an ASCII letter, and dropping it would leave an id that matches no chip, so the save
  stops, names the ids that hold such a character and keeps the form as typed.
- `NOT_PAID` in field 0 of an open-list line: the chips are kept; the bib is given at the start.
- A line without a bib in the protocol list: it cannot be saved (unchanged rule), so no chip is
  bound to nothing.
- The same chip twice on one line: kept once.
- An open list loaded from a file prepared elsewhere, with any character outside ASCII in a chip
  field -- a Cyrillic look-alike, a full-width letter, a full-width comma: the lines load as they
  are, and the registrar is told which lines to open and fix, since "to protocol" copies a line
  verbatim and readers drop what is not ASCII (a lost comma joins two ids).
- A desk reader that types each id followed by Enter: Enter in the chip field adds a separator, so
  one scan after another gives one id each instead of one long id.
- A rider's tag scanned before the registrar picks the rider in the open list: opening a line
  without chips keeps the scan and says so, so it is neither lost nor carried to someone else
  unnoticed; a protocol line opened for a correction shows its own chips.
- A relay team with three stages and bib 15: its riders are 15, 16 and 17, so the chips of its
  first, second and third member bind to those bibs. A team of one stage -- a tandem, a team timed
  as one -- binds every member's chips to its one bib.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Add one field after the registration references (index 11): empty, or chip ids.
  Commas separate the ids of one rider; semicolons separate the riders of a team, in stage order.
  An id is one or more ASCII letters and digits, stored upper case; spaces and any other
  punctuation inside an id are dropped, so an id printed in groups (`E280 1170 0000 020A`) is one
  id; empty ids and repeats are dropped, the first occurrence keeps its place. A rider without
  chips is nothing between two semicolons and keeps the riders after it in place; riders without
  chips at the end are not written, since a team counts its riders by its members.
- **FR-002**: A line built from the form always writes the chip field, even empty, so it has at
  least 12 `#` separators. A line with fewer separators has no chip field and reads as having no
  chips.
- **FR-003**: The form has a visible, editable chip field next to the reference field. Opening a
  line from either list fills it; saving writes it into the new line; saving clears it, as it
  clears the reference field. A character outside ASCII in the chip field stops the save: the
  registrar is told which ids hold one and every form field keeps what was typed, so a wrong
  keyboard layout is caught at the desk. Upper-casing happens without a word. When cleaning drops a
  character inside an id -- a space, a dash -- or a repeated id, the first Save stops and the field
  shows the ids as they will be saved, because only the registrar can tell one id printed in groups
  from two ids pasted without a comma, or see that a repeat left a relay rider without chips; the
  second Save saves them. Chips the form puts in the field (opening a line, adding a member,
  showing cleaned ids) end with a separator, so the next scan is an id of its own. Enter in the
  chip field adds `, ` at the
  cursor, so a desk reader that ends each id with Enter fills the field one id per scan.
- **FR-004**: Every path that copies a line verbatim keeps the chip field and anything after it:
  open to protocol, the backup, the start protocol file, FTP push, the start list upload.
- **FR-005**: A line loaded from the site has an empty chip field. A merge never changes the chips
  of an existing line, including when it links an old line to a registration.
- **FR-006**: "Add into team" appends the added member's chips to the form's chips as the next
  rider, after a semicolon; a member without chips takes an empty place. The member comes
  after the members the team already has (its names, joined by " / ", or by `<BR>` in a relay from
  the site), not after the riders its
  chip field lists, which is empty for a team saved without chips; when the field already lists
  more riders, the member comes after them; on a form with no team yet, the chips typed there are
  the first member's. Repeats stay until Save, which
  shows them dropped. It keeps the team's stage count: the member's own line says "1", and a
  relay's chips bind by it.
- **FR-007**: A chip indicator next to the duplicate one names the first protocol line whose chips
  need a fix -- any character outside ASCII in the field (a line copied verbatim from a file made
  elsewhere never met the form's check), or a relay rider with chips past the last stage (a reserve
  without chips is fine) -- or, failing that, the first line whose chip another line binds to a
  different bib. It leaves the selection where the registrar put it: such a problem lasts until
  fixed, and a jump on every save would aim the next Delete at another rider. An id with a foreign
  letter is compared as typed, so two of them never look alike. A line binds its chips the way the
  chronometers read it: with N > 1 stages and a numeric bib, the k-th rider's chips (counting from
  0) bind to bib + k -- FinishProtocolGenerator and the site number the stage riders so -- and a
  rider past the last stage binds nothing; any other line binds every chip to its bib; a line
  without a bib binds nothing. The same chip twice for one bib is not reported; one chip listed for
  two riders of a relay is.
- **FR-008**: Fields 0-10 keep their position and meaning.

### Key Entities

- **Rider group**: the chip ids of one member of a team, between semicolons, in stage order.

- **Chip id**: the code a chip reader reports for one chip, such as a 96-bit EPC in hexadecimal
  (`E28011700000020A...`) or a transponder code. Bound to exactly one bib through the line that
  carries it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A round trip -- type chips, number, edit, assemble a team, save, restart, merge from
  the site, upload -- ends with every line carrying its chips, proven by Qt-level tests.
- **SC-002**: Every backup and start protocol fixture written by 0.5.x still loads.
- **SC-003**: A line with chips parsed the way FinishProtocolGeneratorPython and the site parse it
  (fields 0-9 by index; field 10 once there are 11 separators) gives the same values as the line
  without chips, proven by unit tests that apply those rules.

## Assumptions

- The site's participants API has no chip field yet, so nothing is read from it; when the site
  starts sending chips, a later change decides whether site or desk wins.
- ChronometerPython and ChronometerAndroid read field 11 from the start protocol file, which they
  can also download from the site's start list (their own specifications).
- No new backup tag is needed: the lists are stored line by line, verbatim.
