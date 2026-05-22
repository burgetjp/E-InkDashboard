from app.config import Settings


def test_defaults():
    s = Settings()
    assert s.port == 8000
    assert s.noaa_grid == "PSR/166,61"
    assert s.refresh_hour_interval == 1


def test_env_override(monkeypatch):
    monkeypatch.setenv("NOAA_GRID", "ABC/1,2")
    monkeypatch.setenv("PORT", "9000")
    s = Settings()
    assert s.port == 9000
    assert s.noaa_grid == "ABC/1,2"
