"""Fleet Telemetry API built with Pixeltable.

    pxt schema update app.py fleet
    pxt service run app.py fleet
"""
from pixeltable.serving import FastAPIRouter

from models import Readings, TableModel  # noqa: F401  (TableModel lets `pxt schema` find the models)
from queries import alerts_since, fleet_board, vehicle_history

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
