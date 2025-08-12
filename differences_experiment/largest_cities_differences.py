from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

import osmnx as ox
from wordcloud import WordCloud


def load_city_names(csv_path: Path) -> list[str]:
    """Load list of city names from the provided CSV file."""
    df = pd.read_csv(csv_path)
    # Only use the top 1000 cities
    return df["Name"].head(1000).tolist()


def _has_footway(highway: object) -> bool:
    """Return True if the highway attribute represents a footway."""
    if isinstance(highway, list):
        return "footway" in highway
    return highway == "footway"


def compute_city_metrics(city: str) -> dict[str, float]:
    """Compute network/feature lengths for a single city in kilometers."""
    metrics = {
        "car_len": 0.0,
        "footway_len": 0.0,
        "sidewalk_len": 0.0,
        "with_sidewalk": 0.0,
    }

    try:
        g_drive = ox.graph_from_place(city, network_type="drive")
        metrics["car_len"] = (
            sum(d.get("length", 0.0) for _, _, d in g_drive.edges(data=True)) / 1000
        )
        metrics["with_sidewalk"] = (
            sum(
                d.get("length", 0.0)
                for _, _, d in g_drive.edges(data=True)
                if d.get("sidewalk") and d.get("sidewalk") != "no"
            )
            / 1000
        )
    except Exception:
        pass

    try:
        g_walk = ox.graph_from_place(city, network_type="walk")
        metrics["footway_len"] = (
            sum(
                d.get("length", 0.0)
                for _, _, d in g_walk.edges(data=True)
                if _has_footway(d.get("highway"))
            )
            / 1000
        )
    except Exception:
        pass

    try:
        gdf_sidewalk = ox.features_from_place(city, tags={"highway": "sidewalk"})
        if not gdf_sidewalk.empty:
            metrics["sidewalk_len"] = gdf_sidewalk.geometry.length.sum() / 1000
    except Exception:
        pass

    return metrics


def build_dataframe(names: list[str]) -> pd.DataFrame:
    """Construct a DataFrame containing metrics for the given cities."""
    rows: list[dict[str, float]] = []
    for city in tqdm(names, desc="Processing cities"):
        row = {"city": city}
        row.update(compute_city_metrics(city))
        rows.append(row)
    return pd.DataFrame(
        rows,
        columns=["city", "car_len", "footway_len", "sidewalk_len", "with_sidewalk"],
    )


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
    df = build_dataframe(city_names)

    boxplot_path = base_dir / "lengths_boxplot.png"
    wordcloud_path = base_dir / "sidewalk_wordcloud.png"

    tasks = [(save_boxplot, boxplot_path), (save_wordcloud, wordcloud_path)]
    for func, path in tqdm(tasks, desc="Generating charts"):
        func(df, path)

    print(f"Saved boxplot to {boxplot_path}")
    print(f"Saved word cloud to {wordcloud_path}")


if __name__ == "__main__":
    main()
