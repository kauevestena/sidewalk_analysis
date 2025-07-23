import unittest
import geopandas as gpd
from sidewalk_creator import SidewalkCreator


class TestSidewalkCreator(unittest.TestCase):
    """
    Unit tests for the SidewalkCreator class.
    """

    def setUp(self):
        """
        Set up the test case.
        """
        self.input_gdf = gpd.read_file('prototypes/test1.geojson')
        self.creator = SidewalkCreator(self.input_gdf)

    def test_initialization(self):
        """
        Test the initialization of the SidewalkCreator class.
        """
        self.assertIsNotNone(self.creator)
        self.assertEqual(self.creator.proj_epsg, self.input_gdf.crs)

    def test_find_intersections(self):
        """
        Test the _find_intersections method.
        """
        intersections = self.creator._find_intersections()
        self.assertIsNotNone(intersections)
        self.assertGreater(len(intersections.geoms), 0)

    def test_split_lines(self):
        """
        Test the _split_lines method.
        """
        self.creator._find_intersections()
        splitted_gdf = self.creator._split_lines()
        self.assertIsNotNone(splitted_gdf)
        self.assertGreater(len(splitted_gdf), 0)

    def test_create_sidewalks(self):
        """
        Test the _create_sidewalks method.
        """
        self.creator._find_intersections()
        self.creator._split_lines()
        sidewalks = self.creator._create_sidewalks()
        self.assertIsNotNone(sidewalks)
        self.assertGreater(len(sidewalks), 0)

    def test_create_crossings(self):
        """
        Test the _create_crossings method.
        """
        self.creator._find_intersections()
        self.creator._split_lines()
        self.creator._create_sidewalks()
        crossings = self.creator._create_crossings()
        self.assertIsNotNone(crossings)
        self.assertGreater(len(crossings), 0)

    def test_process(self):
        """
        Test the process method.
        """
        sidewalks, crossings = self.creator.process()
        self.assertIsNotNone(sidewalks)
        self.assertIsNotNone(crossings)
        self.assertGreater(len(sidewalks), 0)
        self.assertGreater(len(crossings), 0)


if __name__ == '__main__':
    unittest.main()
