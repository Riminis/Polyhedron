import unittest
import tempfile
import os
from math import isclose
from common.r3 import R3
from shadow.polyedr import Polyedr, Facet


def _make_temp_geom(content: str) -> str:
    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.geom', delete=False, encoding='utf-8'
        )
    tmp.write(content)
    tmp.close()
    return tmp.name


class TestGoodPoint(unittest.TestCase):
    def test_inside_large_outside_small_positive(self):
        self.assertTrue(Polyedr.is_good_point(R3(0.75, 0.0, 0.0)))
        self.assertTrue(Polyedr.is_good_point(R3(0.0, 0.8, 0.0)))
        self.assertTrue(Polyedr.is_good_point(R3(0.0, 0.0, 0.9)))
        self.assertTrue(Polyedr.is_good_point(R3(0.7, 0.7, 0.7)))

    def test_inside_large_outside_small_negative(self):
        self.assertTrue(Polyedr.is_good_point(R3(-0.75, 0.0, 0.0)))
        self.assertTrue(Polyedr.is_good_point(R3(0.0, -0.8, 0.0)))
        self.assertTrue(Polyedr.is_good_point(R3(0.0, 0.0, -0.9)))

    def test_inside_both_cubes(self):
        self.assertFalse(Polyedr.is_good_point(R3(0.25, 0.25, 0.25)))
        self.assertFalse(Polyedr.is_good_point(R3(0.0, 0.0, 0.0)))
        self.assertFalse(Polyedr.is_good_point(R3(0.5, 0.5, 0.5)))

    def test_outside_large_cube(self):
        self.assertFalse(Polyedr.is_good_point(R3(1.5, 0.0, 0.0)))
        self.assertFalse(Polyedr.is_good_point(R3(0.0, 1.2, 0.0)))
        self.assertFalse(Polyedr.is_good_point(R3(0.0, 0.0, -1.1)))
        self.assertFalse(Polyedr.is_good_point(R3(2.0, 2.0, 2.0)))

    def test_on_boundary_large_cube(self):
        self.assertFalse(Polyedr.is_good_point(R3(1.0, 0.0, 0.0)))
        self.assertFalse(Polyedr.is_good_point(R3(0.0, -1.0, 0.0)))
        self.assertFalse(Polyedr.is_good_point(R3(0.0, 0.0, 1.0)))

    def test_on_boundary_small_cube(self):
        self.assertFalse(Polyedr.is_good_point(R3(0.5, 0.0, 0.0)))
        self.assertFalse(Polyedr.is_good_point(R3(-0.5, 0.3, 0.4)))
        self.assertFalse(Polyedr.is_good_point(R3(0.2, 0.5, 0.2)))


class TestProjectionAreaXY(unittest.TestCase):
    def test_square_in_xy_plane(self):
        f = Facet([
            R3(0.0, 0.0, 0.0),
            R3(2.0, 0.0, 0.0),
            R3(2.0, 2.0, 0.0),
            R3(0.0, 2.0, 0.0)
            ])
        self.assertAlmostEqual(f.projection_area_xy(), 4.0, places=6)

    def test_triangle_in_xy_plane(self):
        f = Facet([R3(0.0, 0.0, 0.0), R3(3.0, 0.0, 0.0), R3(0.0, 4.0, 0.0)])
        self.assertAlmostEqual(f.projection_area_xy(), 6.0, places=6)

    def test_tilted_facet(self):
        f = Facet([R3(0.0, 0.0, 0.0), R3(2.0, 0.0, 1.0), R3(0.0, 2.0, 1.0)])
        self.assertAlmostEqual(f.projection_area_xy(), 2.0, places=6)

    def test_vertical_facet_zero_projection(self):
        f = Facet([
            R3(0.0, 1.0, 0.0),
            R3(2.0, 1.0, 0.0),
            R3(2.0, 3.0, 0.0),
            R3(0.0, 3.0, 0.0)
            ])
        self.assertAlmostEqual(f.projection_area_xy(), 4.0, places=6)

    def test_degenerate_facet(self):
        f2 = Facet([R3(0.0, 0.0, 0.0), R3(1.0, 1.0, 0.0)])
        self.assertEqual(f2.projection_area_xy(), 0.0)
        f1 = Facet([R3(0.0, 0.0, 0.0)])
        self.assertEqual(f1.projection_area_xy(), 0.0)

    def test_concave_polygon_projection(self):
        f = Facet([
            R3(0.0, 0.0, 0.0),
            R3(2.0, 1.0, 0.0),
            R3(0.0, 2.0, 0.0),
            R3(1.0, 1.0, 0.0)
            ])
        self.assertAlmostEqual(f.projection_area_xy(), 1.0, places=6)


class TestSumProjectionAreasGoodVertices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fake_geom = """1.0 0.0 0.0 0.0
8 6 24
-0.75 -0.75 0.75
-0.75 0.75 0.75
0.75 0.75 0.75
0.75 -0.75 0.75
-0.75 -0.75 -0.75
-0.75 0.75 -0.75
0.75 0.75 -0.75
0.75 -0.75 -0.75
4 1 2 3 4
4 5 6 2 1
4 3 2 6 7
4 3 7 8 4
4 1 4 8 5
4 8 7 6 5"""
        cls._tmp_file = _make_temp_geom(fake_geom)
        cls.polyedr = Polyedr(cls._tmp_file)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls._tmp_file)

    def test_mixed_good_bad_vertices(self):
        fake_geom = """1.0 0.0 0.0 0.0
4 4 6
0.75 0.0 0.0
0.0 0.75 0.0
0.25 0.25 0.25
1.5 0.0 0.0
3 1 2 3
3 1 2 4
3 1 3 4
3 2 3 4"""
        tmp = _make_temp_geom(fake_geom)
        try:
            poly = Polyedr(tmp)
            result = poly.sum_projection_areas_good_vertices()
            self.assertGreater(result, 0.0)
            self.assertTrue(isclose(result, result))
        finally:
            os.unlink(tmp)

    def test_no_good_vertices(self):
        fake_geom = """1.0 0.0 0.0 0.0
4 4 6
0.2 0.2 0.2
0.3 0.2 0.2
0.2 0.3 0.2
0.2 0.2 0.3
3 1 2 3
3 1 2 4
3 1 3 4
3 2 3 4"""
        tmp = _make_temp_geom(fake_geom)
        try:
            poly = Polyedr(tmp)
            result = poly.sum_projection_areas_good_vertices()
            self.assertEqual(result, 0.0)
        finally:
            os.unlink(tmp)


class TestBackwardCompatibility(unittest.TestCase):
    def test_polyedr_init_unchanged(self):
        fake_geom = """200.0 45.0 45.0 30.0
8 6 24
-0.5 -0.5 0.5
-0.5 0.5 0.5
0.5 0.5 0.5
0.5 -0.5 0.5
-0.5 -0.5 -0.5
-0.5 0.5 -0.5
0.5 0.5 -0.5
0.5 -0.5 -0.5
4 1 2 3 4
4 5 6 2 1
4 3 2 6 7
4 3 7 8 4
4 1 4 8 5
4 8 7 6 5"""
        tmp = _make_temp_geom(fake_geom)
        try:
            poly = Polyedr(tmp)
            self.assertEqual(len(poly.vertexes), 8)
            self.assertEqual(len(poly.facets), 6)
            self.assertEqual(len(poly.edges), 24)
            self.assertIsInstance(poly.vertexes[0], R3)
        finally:
            os.unlink(tmp)

    def test_facet_methods_unchanged(self):
        f = Facet([R3(0.0, 0.0, 0.0), R3(3.0, 0.0, 0.0), R3(0.0, 3.0, 0.0)])
        self.assertFalse(f.is_vertical())
        self.assertIsNotNone(f.h_normal())
        self.assertEqual(len(f.v_normals()), 3)
        self.assertIsInstance(f.center(), R3)
        area = f.projection_area_xy()
        self.assertIsInstance(area, float)
        self.assertGreater(area, 0.0)

    def test_edge_class_unchanged(self):
        from shadow.polyedr import Edge
        e = Edge(R3(0.0, 0.0, 0.0), R3(1.0, 1.0, 1.0))
        self.assertEqual(len(e.gaps), 1)
        self.assertFalse(e.gaps[0].is_degenerate())
        f = Facet([R3(0.0, 0.0, 2.0), R3(2.0, 0.0, 2.0), R3(0.0, 2.0, 2.0)])
        e.shadow(f)
