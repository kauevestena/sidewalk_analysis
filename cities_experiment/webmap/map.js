const map = new maplibregl.Map({
    container: 'map',
    style: 'https://api.maptiler.com/maps/streets/style.json?key=get_your_own_OpIi9ZULNHzrESv6T2vL', // Replace with your MapTiler key
    center: [0, 20],
    zoom: 1
});

map.on('load', () => {
    map.addSource('cities', {
        type: 'geojson',
        data: 'cities_data.geojson'
    });

    map.addLayer({
        id: 'cities-layer',
        type: 'circle',
        source: 'cities',
        paint: {
            'circle-radius': [
                'interpolate',
                ['linear'],
                ['get', 'car_len_km'],
                0, 2,
                50000, 20
            ],
            'circle-color': [
                'interpolate',
                ['linear'],
                ['get', 'foot_to_car_ratio'],
                0, '#ff0000', // Red
                0.5, '#ffff00', // Yellow
                1, '#00ff00'  // Green
            ],
            'circle-opacity': 0.7,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#000000'
        }
    });

    // Create a popup, but don't add it to the map yet.
    const popup = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false
    });

    map.on('mouseenter', 'cities-layer', (e) => {
        // Change the cursor style as a UI indicator.
        map.getCanvas().style.cursor = 'pointer';

        const coordinates = e.features[0].geometry.coordinates.slice();
        const properties = e.features[0].properties;

        // Create popup content
        const popupContent = `
            <strong>${properties.city}</strong>, ${properties.country_code}<br/>
            Population: ${properties.population.toLocaleString()}<br/>
            Car network: ${Math.round(properties.car_len_km).toLocaleString()} km<br/>
            Foot network: ${Math.round(properties.footway_len_km).toLocaleString()} km<br/>
            Foot/Car Ratio: ${properties.foot_to_car_ratio.toFixed(2)}
        `;

        // Ensure that if the map is zoomed out such that multiple
        // copies of the feature are visible, the popup appears
        // over the copy being pointed to.
        while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
            coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
        }

        // Populate the popup and set its coordinates
        // based on the feature found.
        popup.setLngLat(coordinates).setHTML(popupContent).addTo(map);
    });

    map.on('mouseleave', 'cities-layer', () => {
        map.getCanvas().style.cursor = '';
        popup.remove();
    });
});
