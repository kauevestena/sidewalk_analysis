from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# Sample data for demonstration purposes
DATA_SAMPLE = {
    "Tokyo": {
        "car_len": 8332.788314397883,
        "footway_len": 3390.8064492946273,
        "sidewalk_len": 1920.057358071414,
        "with_sidewalk": 292.7343003084041,
    },
    "Delhi": {
        "car_len": 6630.787824393951,
        "footway_len": 249.04426524784097,
        "sidewalk_len": 27.31638405980001,
        "with_sidewalk": 34.80184147390246,
    },
    "Shanghai": {
        "car_len": 3037.269177363178,
        "footway_len": 448.3296173033003,
        "sidewalk_len": 56.49890597846692,
        "with_sidewalk": 29.803722922282184,
    },
}


def load_city_names(csv_path: Path) -> list[str]:
    """Load list of city names from the provided CSV file."""
    df = pd.read_csv(csv_path)
    return df["Name"].tolist()


def build_dataframe(names: list[str], metrics: dict[str, dict[str, float]]) -> pd.DataFrame:
    """Construct a DataFrame containing metrics for the given cities."""
    rows = []
    for city in names:
        if city in metrics:
            row = {"city": city}
            row.update(metrics[city])
            rows.append(row)
    return pd.DataFrame(rows)


def save_boxplot(df: pd.DataFrame, out_path: Path) -> None:
    """Save a boxplot comparing length metrics across cities."""
    ax = df[["car_len", "footway_len", "sidewalk_len", "with_sidewalk"]].plot(kind="box")
    ax.set_ylabel("Length (km)")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def save_wordcloud(df: pd.DataFrame, out_path: Path) -> None:
    """Create a word cloud weighted by sidewalk presence."""
    frequencies = {row.city: row.with_sidewalk for row in df.itertuples()}
    wc = WordCloud(width=800, height=400, background_color="white")
    wc.generate_from_frequencies(frequencies)
    wc.to_file(out_path)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    csv_path = base_dir.parent / "prototypes" / "biggest_cities.csv"

    city_names = load_city_names(csv_path)
    df = build_dataframe(city_names, DATA_SAMPLE)

    boxplot_path = base_dir / "lengths_boxplot.png"
    wordcloud_path = base_dir / "sidewalk_wordcloud.png"

    save_boxplot(df, boxplot_path)
    save_wordcloud(df, wordcloud_path)

    print(f"Saved boxplot to {boxplot_path}")
    print(f"Saved word cloud to {wordcloud_path}")


if __name__ == "__main__":
    main()
