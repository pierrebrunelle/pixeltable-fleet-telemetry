<!-- pixeltable-example-app: 20260927-fleet-telemetry -->
# Fleet Telemetry API built with Pixeltable

[![Built with Pixeltable](https://img.shields.io/badge/built%20with-Pixeltable-5b4bff)](https://pixeltable.com)
[![PyPI - pixeltable](https://img.shields.io/pypi/v/pixeltable?label=pixeltable)](https://pypi.org/project/pixeltable/)
[![GitHub stars](https://img.shields.io/github/stars/pixeltable/pixeltable?style=social)](https://github.com/pixeltable/pixeltable)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

Ingest vehicle telemetry (speed, engine temperature, fuel) and query it fast. Readings are declared with explicit **B-tree indexes** on `vehicle_id`, `fleet`, `status` and `recorded_at`, so the per-vehicle history, fleet status board and "alerts since" queries stay index-backed as the table grows. A two-step **UDF chain** scores each reading's severity and turns the score into an alert label, recomputed automatically if a reading is corrected.

[Pixeltable](https://pixeltable.com) is open-source, Python-native **multimodal AI data infrastructure**: tables, incremental computed columns, UDFs, indexes and serving in one library, running locally or on Pixeltable Cloud.

> ⭐ **Like this example?** Star [pixeltable/pixeltable](https://github.com/pixeltable/pixeltable) on GitHub. It helps other developers find it.

## What this example shows

- **B-tree indexes** declared on the model (`__indexes__`) back the lookup queries
- **Incremental computed columns** powered by plain Python UDFs (`@pxt.udf`)
- **Reads and writes**: Json columns, primary-key updates and deletes, and quick inspection with the `pxt` CLI (`pxt rows`, `pxt get`, `pxt count`)
- **FastAPI serving**: one `FastAPIRouter` turns tables and `@pxt.query` functions into typed REST routes (insert, update, delete, compute and query) with OpenAPI docs
- **Importable UDF module**: UDFs in `udfs.py`, tables in `models.py`, queries in `queries.py`, routes in `app.py` (Pixeltable resolves UDFs by module path)
- **`pixeltable.toml`** declares a local database and a **Pixeltable Cloud** database, so the same code deploys with `pxt db update`

## Indexes are part of the model

```python
class Readings(TableModel, name='readings', has_default_idxs=False):
    ...
    __indexes__ = [pxt.BtreeIndex(vehicle_id), pxt.BtreeIndex(fleet),
                   pxt.BtreeIndex(status), pxt.BtreeIndex(recorded_at)]
```

`has_default_idxs=False` turns off the default per-column indexes, so you choose exactly what gets indexed. `pxt schema update` creates them. Add one to the list and rerun it to build a new index in place. Dropping one needs `--allow-destructive`. `pxt idxs fleet/readings` lists them.

## Severity pipeline

`severity_score(speed_kph, engine_temp_c, fuel_pct)` → `severity` (0-100) → `alert_label(severity)` → `alert` (`ok`, `watch`, `critical`). Because `alert` depends on `severity`, correcting a reading with `POST /readings/correct` recomputes both, in order.

## What's inside

| File | What it is |
|------|------------|
| `app.py` | The API: one `FastAPIRouter` wiring the tables and queries into REST routes |
| `client_demo.py` | Score, ingest, correct and query telemetry readings through the API |
| `models.py` | Tables declared as Python classes: columns, computed columns, indexes |
| `pixeltable.toml` | Project config: the local database plus a Pixeltable Cloud database (sizing, deploy excludes) |
| `queries.py` | `@pxt.query` functions served as query routes |
| `seed.py` | Seed 60 synthetic readings for 6 vehicles in 2 fleets |
| `udfs.py` | Pixeltable UDFs (`@pxt.udf`) in their own importable module |
| `requirements.txt` / `pyproject.toml` | Dependencies (`pixeltable[serve]>=0.7.14`) |

**Tables**

| Table | Stored columns | Computed columns |
|-------|---------|------------------|
| `readings` | `vehicle_id`, `fleet`, `status`, `recorded_at`, `speed_kph`, `engine_temp_c`, `fuel_pct` | `id`, `severity`, `alert`, `tag` |

**API routes** (service `telemetry_api`)

| Method | Path | Kind | Backed by | Notes |
|--------|------|------|-----------|-------|
| `POST` | `/readings` | insert | `Readings` |  |
| `POST` | `/readings/correct` | update | `Readings` |  |
| `POST` | `/readings/delete` | delete | `Readings` |  |
| `POST` | `/score` | compute | `Readings` |  |
| `GET` | `/vehicles/history` | query | `vehicle_history` |  |
| `GET` | `/alerts` | query | `alerts_since` |  |
| `GET` | `/fleets/board` | query | `fleet_board` |  |

## Quickstart

Requires Python 3.11+ and `pixeltable[serve]>=0.7.14`.

```bash
git clone https://github.com/pierrebrunelle/pixeltable-fleet-telemetry.git
cd pixeltable-fleet-telemetry
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create the tables in a local catalog directory named `fleet`
pxt schema update app.py fleet

python seed.py fleet
pxt service run app.py fleet --port 8000   # open http://localhost:8000/docs
python client_demo.py                     # in another terminal
pxt idxs fleet/readings                   # the four B-tree indexes
```

Try it:

```bash
curl -s 'localhost:8000/vehicles/history?vehicle_id=V101'
curl -s 'localhost:8000/alerts?since=2026-09-27T12:00:00'
```

## Deploy to Pixeltable Cloud

The same `app.py` runs on [Pixeltable Cloud](https://pixeltable.com). Sign in (or get a free trial database with `pxt new`), point the second database entry in `pixeltable.toml` at your own database, then deploy:

```bash
pxt login                       # or: export PIXELTABLE_API_KEY=<your-api-key>
# edit pixeltable.toml: name = 'pxt://<your-org>:<your-db>'
pxt db update pxt://<your-org>:<your-db>                 # build the image and upload the project
pxt schema update app.py pxt://<your-org>:<your-db>/fleet   # create the tables in the hosted database
pxt service update app.py pxt://<your-org>:<your-db>/fleet  # start the API there
pxt service list pxt://<your-org>:<your-db>              # list hosted services
```

Hosted routes require an API key: send it in the `X-api-key` header (for example `-H "X-api-key: $PIXELTABLE_API_KEY"`). Keep keys in environment variables or `pxt secret set`, never in code.

## Code walkthrough

**1. Business logic is plain Python, in `udfs.py`.** A `@pxt.udf` function can be used as a column expression. Pixeltable records UDFs by module path (`udfs.severity_score`), so they live in their own importable module rather than inline in the app: the daemon, serving workers and Pixeltable Cloud import it again by that path.

```python
# udfs.py
@pxt.udf
def severity_score(speed_kph: float, engine_temp_c: float, fuel_pct: float | None) -> int:
    """0-100: overspeed, overheating and low fuel each add points."""
    score = 0
    score += min(40, max(0, int((speed_kph - 100) * 1.5)))
    score += min(45, max(0, int((engine_temp_c - 95) * 3)))
    if fuel_pct is not None and fuel_pct < 10:
        score += 15
    return min(score, 100)
```

**2. Tables are Python classes (`models.py`).** Annotated attributes are stored columns; attributes assigned an expression are **computed columns** (`id`, `severity`, `alert`, `tag`), evaluated incrementally on every insert or update and recomputed when their inputs change. Indexes live next to the columns.

```python
# models.py
class Readings(TableModel, name='readings', has_default_idxs=False):
    id = pxt.Column(value=pxtf.uuid.uuid7(), primary_key=True)
    vehicle_id: pxt.String
    fleet: pxt.String
    status: pxt.String              # moving / idle / parked
    recorded_at: pxt.String         # ISO-8601, sortable
    speed_kph: pxt.Float
    engine_temp_c: pxt.Float
    fuel_pct: pxt.Float | None

    severity = severity_score(speed_kph, engine_temp_c, fuel_pct)
    alert = alert_label(severity)   # chained on another computed column
    tag = vehicle_tag(fleet, vehicle_id)

    __indexes__ = [pxt.BtreeIndex(vehicle_id), pxt.BtreeIndex(fleet),
                   pxt.BtreeIndex(status), pxt.BtreeIndex(recorded_at)]
```

**3. Queries are functions (`queries.py`).** `@pxt.query` wraps a Pixeltable query so it can be called from Python or exposed as a route:

```python
# queries.py
@pxt.query
def vehicle_history(vehicle_id: str):
    """All readings for one vehicle, newest first (uses the vehicle_id index)."""
    return Readings.where(Readings.vehicle_id == vehicle_id).select(
        Readings.recorded_at, Readings.speed_kph, Readings.engine_temp_c, Readings.severity, Readings.alert
    ).order_by(Readings.recorded_at, asc=False)
```

**4. One router, a full REST API.** `FastAPIRouter` generates request/response models from the column types, validates input, and publishes OpenAPI docs at `/docs`:

```python
# app.py
telemetry_api = FastAPIRouter(name='telemetry_api')
telemetry_api.add_insert_route(
    Readings, path='/readings',
    inputs=[Readings.vehicle_id, Readings.fleet, Readings.status, Readings.recorded_at, Readings.speed_kph,
            Readings.engine_temp_c, Readings.fuel_pct],
    outputs=[Readings.id, Readings.severity, Readings.alert],
)
telemetry_api.add_update_route(Readings, path='/readings/correct',
                               inputs=[Readings.speed_kph, Readings.engine_temp_c, Readings.fuel_pct],
                               outputs=[Readings.id, Readings.severity, Readings.alert])
telemetry_api.add_delete_route(Readings, path='/readings/delete')
telemetry_api.add_compute_route(Readings, path='/score',
                                inputs=[Readings.speed_kph, Readings.engine_temp_c, Readings.fuel_pct],
                                outputs=[Readings.severity, Readings.alert])
telemetry_api.add_query_route(path='/vehicles/history', query=vehicle_history, method='get')
telemetry_api.add_query_route(path='/alerts', query=alerts_since, method='get')
telemetry_api.add_query_route(path='/fleets/board', query=fleet_board, method='get')
```

## Learn more

- 🌐 Website: https://pixeltable.com
- 📚 Docs: https://docs.pixeltable.com
- 💻 Source: https://github.com/pixeltable/pixeltable (⭐ star it if Pixeltable is useful to you)
- 📦 PyPI: https://pypi.org/project/pixeltable/

---

<sub>Built as part of a daily series of Pixeltable example apps · Pixeltable 0.7.14 · Python, FastAPI, incremental computed columns · Licensed under Apache-2.0.</sub>
