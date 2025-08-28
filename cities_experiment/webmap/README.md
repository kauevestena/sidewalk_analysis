# Cities: Walk vs Car Interactive Map

This is an interactive web map that visualizes data on the balance between car and pedestrian infrastructure in cities around the world.

## How to run

To view the map, you need to run a local web server. The easiest way to do this is with Python's built-in HTTP server.

1.  **Get a MapTiler API Key:** The map uses MapTiler for the base map tiles. You will need to get a free API key from [MapTiler Cloud](https://cloud.maptiler.com/).

2.  **Replace the API Key:** Open `map.js` and replace the placeholder `get_your_own_OpIi9ZULNHzrESv6T2vL` with your actual MapTiler API key.

3.  **Navigate to the `webmap` directory:**
    ```bash
    cd cities_experiment/webmap
    ```

4.  **Start the web server:**
    *If you have Python 3:*
    ```bash
    python3 -m http.server
    ```
    *If you have Python 2:*
    ```bash
    python -m SimpleHTTPServer
    ```

5.  **Open the map in your browser:**
    Navigate to [http://localhost:8000](http://localhost:8000) in your web browser.

You should now see the interactive map.
