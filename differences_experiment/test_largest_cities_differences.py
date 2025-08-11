from pathlib import Path

from differences_experiment.largest_cities_differences import (
    DATA_SAMPLE,
    build_dataframe,
    save_boxplot,
    save_wordcloud,
)


def test_build_dataframe_columns():
    names = ["Tokyo", "Delhi", "Shanghai"]
    df = build_dataframe(names, DATA_SAMPLE)
    expected_cols = ["city", "car_len", "footway_len", "sidewalk_len", "with_sidewalk"]
    assert list(df.columns) == expected_cols
    assert len(df) == 3


def test_save_boxplot(tmp_path):
    df = build_dataframe(["Tokyo", "Delhi"], DATA_SAMPLE)
    out = tmp_path / "boxplot.png"
    save_boxplot(df, out)
    assert out.exists()


def test_save_wordcloud(tmp_path):
    df = build_dataframe(["Tokyo", "Delhi"], DATA_SAMPLE)
    out = tmp_path / "wordcloud.png"
    save_wordcloud(df, out)
    assert out.exists()
