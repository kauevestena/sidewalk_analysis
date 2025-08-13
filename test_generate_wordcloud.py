from cities_experiment.functions import generate_wordcloud

def test_generate_wordcloud_zero_data(tmp_path):
    data = {
        "CityA": {"with_sidewalk": 0},
        "CityB": {"with_sidewalk": 0},
    }
    generate_wordcloud(data, tmp_path)
    output_file = tmp_path / 'sidewalk_wordcloud.png'
    assert output_file.exists()
    assert output_file.stat().st_size > 0

