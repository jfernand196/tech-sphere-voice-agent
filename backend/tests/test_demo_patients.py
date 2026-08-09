from app.api.demo import _DEMO_PATIENTS_PATH, _load_patients


def test_demo_patients_catalog():
    assert _DEMO_PATIENTS_PATH.exists(), _DEMO_PATIENTS_PATH
    _load_patients.cache_clear()
    patients = _load_patients()
    assert len(patients) >= 1
    first = patients[0]
    assert first.nombre
    assert first.procedimiento == "colecistectomía"
    assert first.dia_postop >= 0
    assert first.label in {"verde", "amarillo", "rojo"}
