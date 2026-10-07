"""Fleet Telemetry API built with Pixeltable.

    pxt schema update app.py fleet
    pxt service run app.py fleet
"""
import pixeltable as pxt
import pixeltable.functions as pxtf
from pixeltable.serving import FastAPIRouter

from udfs import alert_label, severity_score, vehicle_tag

# ---- tables ----
TableModel = pxt.model_base()


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


# ---- queries ----
@pxt.query
def vehicle_history(vehicle_id: str):
    """All readings for one vehicle, newest first (uses the vehicle_id index)."""
    return Readings.where(Readings.vehicle_id == vehicle_id).select(
        Readings.recorded_at, Readings.speed_kph, Readings.engine_temp_c, Readings.severity, Readings.alert
    ).order_by(Readings.recorded_at, asc=False)


@pxt.query
def alerts_since(since: str):
    """Non-ok readings recorded at or after a timestamp (uses the recorded_at index)."""
    return Readings.where((Readings.recorded_at >= since) & (Readings.alert != 'ok')).select(
        Readings.tag, Readings.recorded_at, Readings.severity, Readings.alert
    ).order_by(Readings.severity, asc=False)


@pxt.query
def fleet_board(fleet: str, status: str):
    """Vehicles in a fleet with a given status (fleet + status indexes)."""
    return Readings.where((Readings.fleet == fleet) & (Readings.status == status)).select(
        Readings.vehicle_id, Readings.recorded_at, Readings.alert
    ).order_by(Readings.vehicle_id)


# ---- routes ----
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
