# Tasks: Keep each rider's timing chips on the start protocol line

Each task is one commit with the message shown; tests are part of the task they prove. Run
`uv run pre-commit run --all-files` and `uv run pytest` before each commit.

## Phase 1: the field (US1, US4)

- [x] T001 [US1] Add `CHIPS_FIELD`, `has_chips_field`, `split_chips`, `join_chips`,
  `foreign_chip_tokens` to `app/models.py`; `parse_competitor_line` returns `chips`;
  `build_competitor_line` takes `chips=""` and always writes field 11. Unit tests in
  `tests/test_chip_ids.py`: normalisation, old lines, built lines have 12 separators.
  -- `feat(protocol): keep each rider's chip ids in field 11`
- [x] T002 [US4] Tests that a line with chips reads the same fields 0-9 by FinishProtocolGenerator's
  rule and field 10 by the site's rule as the same line without chips, and that 0.5.x backup
  fixtures still load. -- `test(protocol): prove the readers of fields 0-10 ignore the chips`

## Phase 2: the form (US1)

- [ ] T003 [US1] "Chips:" field under "Site entry:"; opening a line fills it; Save writes and
  clears it; Enter adds a separator. Qt tests. -- `feat(form): edit a rider's chip ids next to the site entry`
- [ ] T004 [US1] Save refuses a chip token with a non-ASCII character and names it; the form keeps
  what was typed. Qt tests. -- `feat(form): stop a save on a chip id typed in another keyboard layout`

## Phase 3: copies and merges (US1, US2)

- [ ] T005 [US1, US2] Tests: open to protocol, all to protocol, backup round trip, start protocol
  file, start list upload payload and FTP payload keep field 11 and later fields; a site line has
  an empty field 11; a merge keeps an existing line's chips, also when it links an old line.
  -- `test(protocol): keep the chip field through every copy and merge`

## Phase 4: teams and duplicates (US3)

- [ ] T006 [US3] "Add into team" merges the member's chips in member order without repeats. Qt
  test. -- `feat(team): carry every member's chip ids into the team line`
- [ ] T007 [US3] `duplicate_chip_row` and the indicator. Unit and Qt tests.
  -- `feat(protocol): report a chip id used on two protocol lines`

## Phase 5: documentation

- [ ] T008 Describe field 11 in `specs/app/start-protocol.md` (table, readers, the form field, the
  wrong-layout refusal) and list the feature. -- `docs: describe the chip field of the start line`

## Dependencies

T001 before everything; T003 before T004 and T006; T007 needs T001 only; T008 last.
