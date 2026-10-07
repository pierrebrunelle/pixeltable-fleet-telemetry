"""Telemetry readings with explicit B-tree indexes and a chained computed pipeline."""
import pixeltable as pxt
import pixeltable.functions as pxtf

from udfs import alert_label, severity_score, vehicle_tag

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
