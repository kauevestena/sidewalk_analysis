import geopandas as gpd
from shapely.ops import unary_union, split, polygonize_full, nearest_points, linemerge
from shapely.geometry import MultiPoint, MultiPolygon, Point, LineString, LinearRing, Polygon, MultiLineString
import numpy as np
import pandas as pd


class SidewalkCreator:
    """
    A class to transform a GeoDataFrame of lines into sidewalks and crossings.
    """

    def __init__(self, input_gdf: gpd.GeoDataFrame, default_buffer: float = 5.3):
        """
        Initializes the SidewalkCreator with a GeoDataFrame.

        Args:
            input_gdf: A GeoDataFrame containing LineString geometries.
            default_buffer: The default buffer size for creating sidewalks.
        """
        self.input_gdf = input_gdf
        self.proj_epsg = input_gdf.crs
        self.default_buffer = default_buffer
        self.default_crossing_length = default_buffer * 2
        self.intersections = None
        self.splitted_gdf = None
        self.sidewalks = None
        self.crossings = None

    def _find_intersections(self, return_gdf=False):
        """
        Finds all intersection points between the lines in the input GeoDataFrame.
        """
        intersections_dict = {'names': [], 'geometry': []}

        for i, line in enumerate(self.input_gdf.geometry):
            for j, line2 in enumerate(self.input_gdf.geometry):
                if not i == j:
                    if line.intersects(line2):
                        intersec = line.intersection(line2)
                        intersections_dict['names'].append(f'{i}_{j}')
                        intersections_dict['geometry'].append(intersec)

        if return_gdf:
            return gpd.GeoDataFrame(intersections_dict, crs=self.proj_epsg)
        else:
            self.intersections = MultiPoint(intersections_dict['geometry'])
            return self.intersections

    def _split_lines(self):
        """
        Splits the lines at the intersection points.
        """
        all_lines = unary_union(self.input_gdf.geometry)
        splitted = split(all_lines, self.intersections)
        self.splitted_gdf = self._multigeom_to_gdf(splitted, self.proj_epsg)
        return self.splitted_gdf

    def _create_sidewalks(self):
        """
        Creates sidewalk polygons from the split lines.
        """
        result, dangles, cuts, invalids = polygonize_full(self.splitted_gdf.geometry)

        if hasattr(cuts, 'geoms'):
            for polygon in cuts.geoms:
                self.splitted_gdf = self.splitted_gdf[self.splitted_gdf['geometry'] != polygon]

        proto_blocks, dangles, cuts, invalids = polygonize_full(unary_union(self.splitted_gdf.geometry))
        background_polygon = unary_union(proto_blocks)

        buffers = []
        for line in self.splitted_gdf.geometry:
            buffers.append(line.buffer(self.default_buffer))

        gdf_buffers = self._multigeom_to_gdf(MultiPolygon(buffers), self.proj_epsg)
        union_of_buffers = unary_union(gdf_buffers.geometry)

        symm_diff = background_polygon.symmetric_difference(union_of_buffers)

        symm_diff2 = self._remove_polygons_with_holes(symm_diff)

        rounded_blocks = []
        for block in symm_diff2:
            custom_buffer = block.length * 0.01
            as_buffer = block.buffer(-custom_buffer, join_style=1).buffer(custom_buffer, join_style=1)
            rounded_blocks.append(LinearRing(as_buffer.exterior.coords))

        self.sidewalks = self._multigeom_to_gdf(rounded_blocks, self.proj_epsg)
        return self.sidewalks

    def _create_crossings(self):
        """
        Creates crossing geometries.
        """
        newlines = []
        crossing_points = []

        for line in self.splitted_gdf.geometry:
            P0 = Point(line.coords[0])
            PF = Point(line.coords[-1])

            points_to_add = []

            number_touches_p1 = sum(self.splitted_gdf.intersects(P0))
            number_touches_pf = sum(self.splitted_gdf.intersects(PF))

            occurrences = (number_touches_p1, number_touches_pf)

            if all(x > 2 for x in occurrences):
                if any(x > 3 for x in occurrences):
                    if line.length > 2 * self.default_crossing_length:
                        if number_touches_p1 > 2:
                            points_to_add.append(line.interpolate(self.default_crossing_length))

                        if number_touches_pf > 2:
                            points_to_add.append(line.interpolate(-self.default_crossing_length))
                    else:
                        if number_touches_p1 > 2 or number_touches_pf > 2:
                            points_to_add.append(line.interpolate(0.5, normalized=True))

            if points_to_add:
                crossing_points += points_to_add

        crossings_gdf = self._multigeom_to_gdf(crossing_points, self.proj_epsg)

        distances_dict = {}
        for i, point in enumerate(crossings_gdf.geometry):
            distances = []
            for j, polygon in enumerate(self.sidewalks.geometry):
                distances.append(polygon.distance(point))
            distances_dict[i] = distances

        distances_df = pd.DataFrame(distances_dict)

        crossing_geoms = []
        for column in distances_df.columns:
            crossing_geom_list = []
            two_smallest_block_index = list(distances_df[column].nsmallest(2).keys())
            curr_point = crossings_gdf.iloc[column].geometry

            for i in two_smallest_block_index:
                curr_block = self.sidewalks.iloc[i].geometry
                block_p, _ = nearest_points(curr_block, curr_point)
                if not crossing_geom_list:
                    pos2_point = self._point_between_two(block_p, curr_point)
                    crossing_geom_list = [block_p, pos2_point, curr_point]
                else:
                    pos4_point = self._point_between_two(curr_point, block_p, 2 / 3)
                    crossing_geom_list.append(pos4_point)
                    crossing_geom_list.append(block_p)
            crossing_geoms.append(LineString(crossing_geom_list))

        self.crossings = self._multigeom_to_gdf(crossing_geoms, self.proj_epsg)
        return self.crossings

    def process(self):
        """
        Processes the input GeoDataFrame to create sidewalks and crossings.
        """
        self._find_intersections()
        self._split_lines()
        self._create_sidewalks()
        self._create_crossings()
        return self.sidewalks, self.crossings

    def _multigeom_to_gdf(self, inputgeom, crs):
        """
        Converts a Multi-geometry object to a GeoDataFrame.
        """
        splitted_geoms = {
            'names': [],
            'geometry': []
        }
        if hasattr(inputgeom, 'geoms'):
            geoms = list(inputgeom.geoms)
        else:
            geoms = list(inputgeom)

        for i, subgeom in enumerate(geoms):
            splitted_geoms['names'].append(f'{i}')
            splitted_geoms['geometry'].append(subgeom)

        as_gdf = gpd.GeoDataFrame(splitted_geoms, crs=crs)

        return as_gdf

    def _remove_polygons_with_holes(self, input_geomcontainer):
        """
        Removes polygons with holes from a geometry container.
        """
        if not isinstance(input_geomcontainer, list):
            input_geomcontainer = list(input_geomcontainer.geoms)

        output_geoms = []
        for i, geom in enumerate(input_geomcontainer):
            if geom.geom_type == "Polygon":
                if not list(geom.interiors):
                    output_geoms.append(geom)

        return output_geoms

    def _point_between_two(self, p1, p2, ratio=1 / 3):
        """
        Finds a point between two points.
        """
        line_geom = LineString([p1, p2])
        return line_geom.interpolate(ratio, normalized=True)
