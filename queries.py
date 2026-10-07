"""Index-backed queries over the readings table."""
import pixeltable as pxt

from models import Readings


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
