from pathlib import Path
from unittest.mock import patch

from differences_experiment.largest_cities_differences import (
    build_dataframe,
    save_boxplot,
    save_wordcloud,
)

SAMPLE_METRICS = {
    "Tokyo": {
        "car_len": 1.0,
        "footway_len": 2.0,
        "sidewalk_len": 0.5,
        "with_sidewalk": 0.25,
    },
    "Delhi": {
        "car_len": 2.0,
        "footway_len": 3.0,
        "sidewalk_len": 0.7,
        "with_sidewalk": 0.35,
    },
    "Shanghai": {
        "car_len": 3.0,
        "footway_len": 4.0,
        "sidewalk_len": 0.9,
        "with_sidewalk": 0.45,
    },
}


def fake_metrics(city: str) -> dict[str, float]:
    return SAMPLE_METRICS[city]


def test_build_dataframe_columns():
    names = ["Tokyo", "Delhi", "Shanghai"]
    with patch(
        "differences_experiment.largest_cities_differences.compute_city_metrics",
        side_effect=fake_metrics,
    ):
        df = build_dataframe(names)
    expected_cols = ["city", "car_len", "footway_len", "sidewalk_len", "with_sidewalk"]
    assert list(df.columns) == expected_cols
    assert len(df) == 3


def test_save_boxplot(tmp_path: Path):
    with patch(
        "differences_experiment.largest_cities_differences.compute_city_metrics",
        side_effect=fake_metrics,
    ):
        df = build_dataframe(["Tokyo", "Delhi"])
    out = tmp_path / "boxplot.png"
    save_boxplot(df, out)
    assert out.exists()


def test_save_wordcloud(tmp_path: Path):
    with patch(
        "differences_experiment.largest_cities_differences.compute_city_metrics",
        side_effect=fake_metrics,
    ):
        df = build_dataframe(["Tokyo", "Delhi"])
    out = tmp_path / "wordcloud.png"
    save_wordcloud(df, out)
    assert out.exists()
