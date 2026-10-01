---
name: cycling-site-api
description: How the referee desktop apps exchange data with the cycling site -- the endpoints, how a competition is addressed, how device_id and client_revision decide what the site keeps, the line formats, and the rules an HTTP client here must follow. Use when touching app/http_io.py, an upload or download path, or anything that reads or writes competition data on the site.
---

# The cycling-site API

Two desktop apps talk to the same site. Start Protocol Maker reads participants and
pushes the start list; WindowsChronometer pushes group starts and crossings. Both use
`urllib` from the standard library, with a 10 second timeout, and no dependency on a
HTTP client library.

## Addressing a competition

Every call carries a `competition_token` -- a UUID the organizer copies from the
competition detail page on the site. The site URL and the token are entered in the UI
and stored in the app's local config; they are per-event credentials, so never
hardcode one, never commit one, and never put one in a test fixture beyond an obvious
placeholder.

## Reading

`GET /api/v1/participants/?competition_token=<token>` returns an object with
`participants`, `categories` and `competition_title`. A category carries `id`, `name`,
`laps`, `bib_from` and `bib_to`; the bib range becomes the group's number range, which
is what the "Get number" button draws from. The chronometer reads the same endpoint
just for group names.

## Writing

All uploads are POSTs with a JSON body of `competition_token`, `device_id`, `items`,
`client_revision`, and return `{"count": n}`:

- `POST /api/v1/start-list/` -- the start protocol (Start Protocol Maker)
- `POST /api/v1/group-times/` -- group start times (chronometer)
- `POST /api/v1/finish-times/` -- finish crossings, control point 0 (chronometer)
- `POST /api/v1/remote-points/` -- crossings at point 1..N; the body also carries
  `point_number` (chronometer)

## device_id and client_revision

`device_id` is a stable per-machine id, generated once and persisted, so the site can
tell several referees' uploads apart. An upload **replaces** everything previously
stored for that device and stream -- it is a snapshot, not an append, so always send
the full current list.

`client_revision` is a per-device counter that must increase with every send. The
server rejects a stale or reordered snapshot with **HTTP 409**, which is how a delayed
upload is stopped from overwriting a newer one. Persist the counter next to the data,
bump it before sending, and never reset it.

## Line formats

`items` are the same lines the apps keep on disk, `#` separated and `#` terminated:

- start protocol: `number#name#group#laps#stage#year_of_birth#team#city#comment#time_shift#`
- group start: `group#time#`
- crossing: `number#time#status#`, where status is `finish`, `nextLap`,
  `DSQ` or `DSQ: <reason>`

`time` is `days hh:mm:ss.mmm`, for example `0 12:00:00.000`.

## Rules for the client

These come from bugs that shipped; a client that skips them can take the app down at
a registration desk.

- **Normalize every failure into `ValueError`.** `urllib` wraps only what fails while
  sending: `HTTPError` and `URLError`. A socket timeout or a dropped connection while
  reading the response arrives as a bare `OSError`, and callers reach these functions
  from Qt slots, where an unhandled exception terminates the application.
- **Validate the body before using it.** A response that is not a JSON object, or a
  `count` that is not a number, must be reported as an invalid response rather than
  raising `TypeError` or `AttributeError` deep in a slot.
- **Report, do not block.** An upload triggered by a timer or by autosave must surface
  its outcome in a status label; only a button the referee just pressed may open a
  dialog.
- **Retry on a timer, not on the next edit.** Registration goes quiet exactly when the
  list matters most, so a failed automatic upload re-arms itself (15s in Start Protocol
  Maker) until it succeeds.
- The chronometer's client has not been hardened the same way yet: `app/http_io.py`
  there still lets `OSError` and a malformed body through.
