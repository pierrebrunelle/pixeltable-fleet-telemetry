"""Pixeltable UDFs for fleet telemetry (recorded by module path, e.g. `udfs.severity_score`)."""
import pixeltable as pxt


@pxt.udf
def severity_score(speed_kph: float, engine_temp_c: float, fuel_pct: float | None) -> int:
    """0-100: overspeed, overheating and low fuel each add points."""
    score = 0
    score += min(40, max(0, int((speed_kph - 100) * 1.5)))
    score += min(45, max(0, int((engine_temp_c - 95) * 3)))
    if fuel_pct is not None and fuel_pct < 10:
        score += 15
    return min(score, 100)


@pxt.udf
def alert_label(severity: int) -> str:
    return 'critical' if severity >= 60 else ('watch' if severity >= 25 else 'ok')


@pxt.udf
def vehicle_tag(fleet: str, vehicle_id: str) -> str:
    return f'{fleet.upper()}/{vehicle_id}'
