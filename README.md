# ANPR Gate System

An automatic number plate recognition (ANPR) system that reads vehicle plates from an existing campus camera feed, checks them against a registered vehicle database, and opens a barrier arm gate — no RFID tap required. Built for a college gate where bikers previously had to stop on a slope to tap an RFID card in the rain.

The existing RFID system remains completely untouched. If ANPR does not fire (bad weather, dirty plate, new vehicle), the person taps their card as usual.

---

## How It Works

1. A Python process reads frames from the existing IP camera via RTSP every 500 ms.
2. OpenCV detects a rectangular plate-shaped region in each frame.
3. EasyOCR reads the text from the cropped region and returns a confidence score.
4. If confidence is **≥ 85%**, the plate string is normalised (uppercase, stripped) and checked against the database.
5. **Registered + active vehicle** → relay fires, gate opens for 8 seconds, log entry written.
6. **Unknown or inactive vehicle** → snapshot saved, alert written to DB, guard notified via WhatsApp.
7. The RFID system operates independently and handles any case ANPR misses.

---

## Features

- **Zero-stop entry** for registered vehicles — bikes pass without halting
- **Confidence threshold gating** — low-quality reads are silently discarded, no false opens
- **Duplicate suppression** — same plate ignored for 30 seconds after a trigger
- **Double-entry detection** — flags vehicles that enter twice without an exit (logged as anomaly, gate still opens)
- **Guard WhatsApp alerts** — unknown plates send a message with plate text and snapshot via Twilio
- **Web admin dashboard** — manage vehicles, view logs, resolve alerts from any browser on the local network
- **CSV bulk import** — migrate the existing college vehicle registry in one upload
- **CSV log export** — filterable export for college records, with CSV-injection protection
- **Fully on-premise** — no cloud dependency; runs on a Raspberry Pi 5 or a mini-PC in the guard room
- **37 automated tests** — unit and integration coverage across all layers

---

## Project Structure

```
anpr/
├── main.py                        # Entry point — starts API + engine
├── config.py                      # All settings via .env
├── requirements.txt
├── .env.example
│
├── anpr_engine/
│   ├── camera.py                  # RTSP frame sampler
│   ├── detector.py                # OpenCV plate region extractor
│   ├── ocr.py                     # EasyOCR wrapper
│   ├── normalizer.py              # Plate string normaliser
│   ├── gate.py                    # Relay trigger (mock / GPIO)
│   └── engine.py                  # Main recognition loop
│
├── backend/
│   ├── main.py                    # FastAPI app + static mounts
│   ├── database.py                # SQLAlchemy engine & session
│   ├── models.py                  # Vehicle, Log, Alert ORM models
│   ├── schemas.py                 # Pydantic request/response schemas
│   ├── crud.py                    # All database operations
│   ├── notifier.py                # Twilio WhatsApp alert sender
│   └── routes/
│       ├── vehicles.py            # Vehicle CRUD + CSV import
│       ├── logs.py                # Log query + CSV export
│       └── alerts.py              # Alert list + resolve
│
├── dashboard/
│   ├── index.html                 # Redirect to vehicles.html
│   ├── vehicles.html              # Vehicle management page
│   ├── logs.html                  # Entry/exit log viewer
│   └── alerts.html                # Guard alert feed
│
├── tests/
│   ├── conftest.py                # Shared in-memory SQLite fixture
│   ├── test_crud.py               # 11 CRUD operation tests
│   ├── test_vehicles_api.py       # 6 vehicle route tests
│   ├── test_logs_api.py           # 3 log route tests
│   ├── test_alerts_api.py         # 4 alert route tests
│   ├── test_normalizer.py         # 5 normaliser tests
│   ├── test_ocr.py                # 3 OCR module tests
│   ├── test_detector.py           # 3 plate detector tests
│   └── test_engine.py             # 2 engine integration tests
```

---

## Requirements

- Python 3.11+
- A camera accessible via RTSP (most IP cameras and NVRs expose this)
- A relay module wired to the gate controller (same trigger point as the existing remote override)
- On Raspberry Pi: GPIO access for the relay pin
- (Optional) A Twilio account for WhatsApp guard alerts

---

## Installation

```bash
git clone <repo-url>
cd anpr
pip install -r requirements.txt
```

> On a headless server or Raspberry Pi, `opencv-python-headless` is used instead of `opencv-python` — no display server required.

---

## Configuration

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `CAMERA_URL` | `rtsp://localhost:554/stream` | RTSP URL of the gate camera |
| `CONFIDENCE_THRESHOLD` | `0.85` | Minimum OCR confidence to act on (0–1) |
| `GATE_CLOSE_DELAY` | `8` | Seconds before gate auto-closes |
| `DUPLICATE_SUPPRESSION_SECONDS` | `30` | Seconds to ignore the same plate after a trigger |
| `GATE_DIRECTION` | `IN` | `IN` for entry camera, `OUT` for exit camera |
| `RELAY_MODE` | `mock` | `mock` (print only) or `gpio` (Raspberry Pi) |
| `RELAY_PIN` | `17` | BCM GPIO pin number for the relay |
| `DATABASE_URL` | `sqlite:///./anpr.db` | SQLAlchemy database URL |
| `SNAPSHOT_DIR` | `snapshots` | Directory to save unknown-plate images |
| `TWILIO_ACCOUNT_SID` | *(empty)* | Twilio account SID — leave empty to disable alerts |
| `TWILIO_AUTH_TOKEN` | *(empty)* | Twilio auth token |
| `TWILIO_FROM_NUMBER` | *(empty)* | Twilio WhatsApp-enabled number (e.g. `+1234567890`) |
| `GUARD_PHONE_NUMBER` | *(empty)* | Guard's WhatsApp number (e.g. `+919876543210`) |

When `TWILIO_ACCOUNT_SID` is empty the notifier prints to stdout instead of sending a message — useful during development.

---

## Running

### Development (no real camera or relay needed)

Start only the API server with the dashboard:

```bash
uvicorn backend.main:app --reload --port 8000
```

Open `http://localhost:8000` in a browser. The dashboard loads immediately. The ANPR engine is not started; you can seed data via the dashboard or the API directly.

### Production (camera + relay connected)

```bash
python main.py
```

This starts two threads:

- **Thread 1 (main)** — ANPR engine loop; reads RTSP stream, fires relay
- **Thread 2 (daemon)** — uvicorn API server on `:8000`

The process blocks on the engine loop. Stop with `Ctrl+C`.

---

## Importing Existing Vehicle Data

Export the college database to a CSV with these columns:

```
plate,owner_name,roll_number,vehicle_type
MH12AB1234,Rahul Sharma,21BCE001,bike
KA05XY9988,Priya Nair,21BCE002,car
```

Then upload via the dashboard (Vehicles → Import CSV) or via API:

```bash
curl -X POST http://localhost:8000/vehicles/import \
  -F "file=@college_vehicles.csv"
```

Response:

```json
{ "imported": 247, "skipped": 3 }
```

Skipped rows are either duplicates or rows with an empty plate field.

---

## API Reference

Interactive docs are available at `http://localhost:8000/docs` when the server is running.

### Vehicles

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/vehicles/` | List all vehicles. Optional `?search=` param filters by plate, name, or roll number |
| `POST` | `/vehicles/` | Register a new vehicle. Returns `201 Created` |
| `PUT` | `/vehicles/{id}` | Update vehicle fields |
| `DELETE` | `/vehicles/{id}` | Soft-deactivate a vehicle (sets `active=false`) |
| `POST` | `/vehicles/import` | Bulk import from CSV. Max 5 MB |

### Logs

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/logs/` | List logs. Filterable by `plate`, `from_dt`, `to_dt`, `anomaly`. Paginated via `skip` / `limit` |
| `GET` | `/logs/export` | Download filtered logs as CSV |

### Alerts

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/alerts/` | List alerts. Optional `?resolved=false` to show only pending. Paginated via `skip` / `limit` |
| `POST` | `/alerts/{id}/resolve` | Mark an alert as resolved |

### Static Assets

| Path | Description |
|---|---|
| `GET` `/` | Serves the web dashboard (redirects to `vehicles.html`) |
| `GET` `/snapshots/{filename}` | Serves saved gate snapshots |

---

## Web Dashboard

Access at `http://localhost:8000` from any device on the same network.

### Vehicles Page (`/vehicles.html`)

- Live stats: total registered, active, inactive
- Search by plate, owner name, or roll number
- Add single vehicle with form validation
- Bulk import via CSV file upload
- Soft-deactivate any active vehicle

### Logs Page (`/logs.html`)

- Entry/exit activity table with direction badges (IN / OUT), confidence bar, and anomaly highlights
- Filter by plate, date range, and anomaly flag
- Stats bar showing totals for the current filtered view
- Export filtered results to CSV

### Alerts Page (`/alerts.html`)

- Table of unknown plate detections with snapshot thumbnail, plate, timestamp, and status
- Pending alerts show a pulsing badge; resolved alerts are dimmed
- Pending alert count shown in the navigation badge and page title
- One-click resolve per alert
- Auto-refreshes every 10 seconds

---

## Hardware Wiring

### Relay Connection

The gate controller has a remote override that opens the gate when two terminals are shorted. Wire a relay module so that:

- Relay **COM** → terminal 1 on gate controller
- Relay **NO** (normally open) → terminal 2 on gate controller

On Raspberry Pi, connect the relay IN pin to GPIO pin 17 (default, configurable via `RELAY_PIN`).

Set `RELAY_MODE=gpio` in `.env` to activate hardware control.

### Camera RTSP URL

Most IP cameras expose a stream at one of these patterns — check your camera manual:

```
rtsp://<ip>:554/stream
rtsp://<ip>:554/ch0
rtsp://<user>:<password>@<ip>:554/stream
```

Set this as `CAMERA_URL` in `.env`.

### Night / Rain Performance

The system uses the existing camera as-is. If OCR accuracy drops below acceptable levels in low light or rain, a small IR floodlight aimed at plate height (₹500–₹1000) will significantly improve results. Alternatively, lower `CONFIDENCE_THRESHOLD` to `0.75` to accept more reads at the cost of occasional false positives.

---

## Twilio WhatsApp Setup

1. Create a free account at [twilio.com](https://www.twilio.com)
2. Enable the WhatsApp Sandbox (for testing) or a dedicated WhatsApp sender (for production)
3. Note your Account SID, Auth Token, and WhatsApp-enabled number
4. Add them to `.env`
5. Have the guard's phone join the Twilio sandbox by sending the join phrase to the Twilio number (sandbox only)

When an unknown plate is detected the guard receives:

```
Unknown vehicle at gate
Plate: KA05XY9988
Time: 2026-06-11T10:32:00+00:00
```

---

## Running Tests

```bash
pytest tests/ -v
```

Expected output: **37 passed**.

```
tests/test_crud.py          11 passed   DB model + CRUD operations
tests/test_vehicles_api.py   6 passed   Vehicle HTTP endpoints
tests/test_logs_api.py       3 passed   Log HTTP endpoints
tests/test_alerts_api.py     4 passed   Alert HTTP endpoints
tests/test_normalizer.py     5 passed   Plate string normaliser
tests/test_ocr.py            3 passed   EasyOCR wrapper
tests/test_detector.py       3 passed   OpenCV plate detector
tests/test_engine.py         2 passed   Engine integration (mocked camera)
```

All tests use an in-memory SQLite database and mocked hardware — no camera, relay, or Twilio credentials required.

---

## Adding a New Vehicle (student brings a second vehicle)

The RFID system covers this automatically as a fallback. To also enable ANPR for the new vehicle:

1. Open `http://localhost:8000` on the guard room PC
2. Go to **Vehicles → Add Vehicle**
3. Enter the plate number, owner name, roll number, and vehicle type
4. Click **Add Vehicle**

The next time that plate appears on camera, the gate will open automatically.

---

## Security Notes

- **No authentication** is currently implemented on the API or dashboard. The system is designed for internal network use only. Before exposing to the campus network, add at minimum an HTTP Basic Auth middleware or restrict access by IP.
- **CORS is fully open** (`allow_origins=["*"]`). Tighten this to the specific origin of the guard room PC for production.
- Twilio credentials are stored as `SecretStr` in pydantic and will not appear in logs or serialised settings output.
- Snapshots of unknown vehicles are stored locally and served over the same `:8000` port — treat this server as internal only.

---

## Known Limitations

- **Single gate** — the system monitors one camera and controls one relay. Multi-gate deployments would require running a separate instance per gate with its own `GATE_DIRECTION` and `CAMERA_URL`.
- **No exit camera by default** — `GATE_DIRECTION=IN` means all logs are recorded as entries. To track exits, set up a second instance with `GATE_DIRECTION=OUT` pointed at an exit-lane camera.
- **GPIO relay blocks the engine thread** — while the relay is held open (default 8 seconds), no new frames are processed. At a low-traffic college gate this is acceptable; a high-volume gate would need an async relay implementation.
- **SQLite concurrency** — adequate for a single gate writing logs at low frequency. If multiple gates write to a shared database, migrate to PostgreSQL via the `DATABASE_URL` setting.

---

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| ANPR / OCR | EasyOCR, OpenCV (headless) |
| Web Framework | FastAPI |
| ORM | SQLAlchemy 2.x |
| Database | SQLite (production-upgradeable to PostgreSQL) |
| Validation | Pydantic v2 |
| Alert Delivery | Twilio WhatsApp / SMS |
| Dashboard | Plain HTML + Tailwind CSS (CDN) + vanilla JS |
| Hardware | Raspberry Pi 5 or any Linux mini-PC |
| Gate Trigger | GPIO relay module |
| Testing | pytest + httpx |

---

## License

MIT
