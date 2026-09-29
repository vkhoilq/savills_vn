# Code Review — `booking_schedule_cli.py` and friends

Captured: review of the Savills/Vista Verde tennis-court auto-booking project, taken from the working command:

```
python booking_schedule_cli.py lqkhoi@gmail.com Ti02ca09 7 5 10 2026 1
```

## What the command does

| Pos | Value | Meaning |
|-----|-------|---------|
| 1 | `lqkhoi@gmail.com` | username (currently **ignored** — see issue #1) |
| 2 | `Ti02ca09` | password (currently **ignored**) |
| 3 | `7` | hour (07:00) |
| 4 | `5` | day in week (5 = Saturday in this codebase: Mon=0…Sat=5, Sun=6) |
| 5 | `10` | month |
| 6 | `2026` | year |
| 7 | `1` | wait flag (1 = sleep until 00:00 before booking) |

**Goal:** at the stroke of midnight, fire parallel `create_booking` requests to reserve the Vista Verde tennis court (amenityId=3) for every Saturday in October 2026 at 7:00, since Savills only opens the next month's bookings at 00:00 on the 1st.

---

## Execution flow
1. `booking_schedule_cli.py` boots → logs in via `Savills(USERNAME, PASSWORD)` from `config.py`.
2. `savills_booking_schedule(sys.argv)` parses `argv[1:]` as `hour, dayinweek, month, year, wait`.
3. If `wait==1`: busy-loops `time.sleep(1)` until local time is exactly 00:00:00.
4. Calls `test_multiple_booking_parallel(...)` → `get_day_times(...)` to enumerate every target Saturday → `ThreadPoolExecutor.submit(create_booking, ...)` for each.

## File map
| File | Role |
|------|------|
| `booking_schedule_cli.py` | CLI entry: login → wait → parallel book Saturdays |
| `savills.py` | `Savills` client: login, `create_booking`, `delete_booking`, `get_bookings`, `get_neighbor_info` |
| `res_client.py` | Generic `BaseRESTClient` with auto re-login on 401 |
| `savills_data.py` | Pydantic models: `Building, Unit, Member, Booking, Neighbor` |
| `gettime.py` | `get_day_times(year, month, dayinweek, hour)` returns all matching slots |
| `vv_neighbor_cli.py` | Bulk-enumerate all residents (security demo) |
| `main.py` | Unused stub |

## API surface (from `savills.py`)
- Login: base64-encoded creds to `accounts-vn…/api/TokenAbAuth/Authenticate` → switch linked account → `LinkedAccountAuthenticate`.
- Booking create: `POST /booking/api/bookings/create` with full body, base64-wrapped.
- Booking cancel: `PUT /booking/api/bookings/resident` (status=`CANCELED`).
- All request bodies are wrapped as `{"data": base64(json)}`.

---

## ⚠️ Things to know before modifying

### 1. CLI credentials are silently ignored
`booking_schedule_cli.py:60` reads `USERNAME,PASSWORD` from `config.py` — your `argv[1]`/`argv[2]` are never consumed. If you intend positional auth, plumb it through to `Savills(...)`.

### 2. The parallel-booking block is short-circuited
`booking_schedule_cli.py:16` has a bare `return` inside `test_multiple_booking_parallel` after `print(lst)`. The `ThreadPoolExecutor` block below it **never runs** in the current file. The "success" you're seeing is login + slot list + midnight wait; the actual `create_booking` calls are dead code. Delete the stray `return` (or comment it out) when you want real bookings.

### 3. Hardcoded `amenityId=3` (Tennis)
`savills.py:178` defaults to amenity 3. Discover alternatives via `GET /booking/api/amenities?isActive=true&buildingId=0&culture=vi` (commented in source).

### 4. Wait loop is 1-second polling
`booking_schedule_cli.py:46-51` checks wall clock every second for the exact 00:00:00 transition. Fine, but there's no skew against the server. If you want tighter accuracy, anchor on `NTP`/`time.monotonic()` or query the server's `/server/time` first.

### 5. Timezone is hardcoded UTC+7
`gettime.py:7-8` builds `tzoffset('UTC+7', 7*3600)`. The Savills API appears to expect Asia/Ho_Chi_Minh (which is UTC+7, no DST). If DST ever bites, prefer `zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")` (stdlib in 3.13).

### 6. `dayinweek` is non-Pythonic
0=Monday, 5=Saturday, 6=Sunday (ISO-ish, but `weekday()` already returns this). Worth renaming or documenting near `savills_booking_schedule`.

### 7. `Booking` model has duplicate field
`savills_data.py:45` declares `createdAt: str` twice — pydantic just keeps the last one. Cleanup before adding logic that reads it.

### 8. `BaseRESTClient._make_request` re-login retries once on 401
If the second attempt also 401s it raises — no token refresh / captcha handling. Safe for now but a future fragility.

### 9. `create_booking` retries 5× on any exception
Including non-transient ones (validation errors, etc.). Consider distinguishing `requests.exceptions.RequestException` from server-side 4xx.

### 10. `Neighbor` model exists but is never used by `Savills`
`vv_neighbor_cli.py` reuses `Member` and stuffs `house_code` into `profilePictureId`. If you formalize neighbor scraping, fill in `Neighbor` properly.

### 11. README is stale
Says `python savills.py` to run, but `savills.py` only has test functions in `__main__`. The real entry is `booking_schedule_cli.py`.

### 12. `requires-python = ">=3.13"` and `.python-version = 3.13`
`uv.lock` and `.venv` are committed-friendly but you're tied to 3.13 features (fine, but worth knowing if you ever share this).

---

## Where to make common changes
| Goal | File:line |
|------|-----------|
| Book a different amenity | `savills.py:178` (`amenityId` default) or pass `amenityId=` from CLI |
| Change weekday/hour range | `gettime.py:11` (`get_day_times` signature) |
| Use CLI-supplied creds | `booking_schedule_cli.py:60` — replace `from config import …` with `argv[1]`, `argv[2]` and shift other indices |
| Actually run the parallel bookings | `booking_schedule_cli.py:17` — remove the dead `return` |
| Add a different "trigger" instead of 00:00 | Replace the `while True: time.sleep(1)` block at lines 45-51 |
| Change retry policy | `savills.py:210-216` |
| Surface booking success/failure to logs | Currently `create_booking` returns `id` or `None`; no aggregation in the CLI loop |
