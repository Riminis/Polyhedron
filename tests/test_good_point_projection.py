import unittest
import tempfile
import os
from math import isclose, pi
from common.r3 import R3
from shadow.polyedr import Polyedr, Facet


def _make_temp_geom(content: str) -> str:
    """Вспомогательная функция: создаёт временный .geom файл"""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.geom', delete=False, encoding='utf-8')
    tmp.write(content.strip())
    tmp.close()
    return tmp.name


class TestGoodPoint(unittest.TestCase):
    """Тесты для статического метода Polyedr.is_good_point (проверка по ИСХОДНЫМ координатам)"""

    def test_inside_large_outside_small_positive(self):
        """Точка внутри большого куба, вне малого (положительные координаты)"""
        self.assertTrue(Polyedr.is_good_point(R3(0.75, 0.0, 0.0)))
        self.assertTrue(Polyedr.is_good_point(R3(0.0, 0.8, 0.0)))
        self.assertTrue(Polyedr.is_good_point(R3(0.0, 0.0, 0.9)))
        self.assertTrue(Polyedr.is_good_point(R3(0.7, 0.7, 0.7)))

    def test_inside_large_outside_small_negative(self):
        """Точка внутри большого куба, вне малого (отрицательные координаты)"""
        self.assertTrue(Polyedr.is_good_point(R3(-0.75, 0.0, 0.0)))
        self.assertTrue(Polyedr.is_good_point(R3(0.0, -0.8, 0.0)))
        self.assertTrue(Polyedr.is_good_point(R3(0.0, 0.0, -0.9)))

    def test_inside_both_cubes(self):
        """Точка внутри обоих кубов — не «хорошая»"""
        self.assertFalse(Polyedr.is_good_point(R3(0.25, 0.25, 0.25)))
        self.assertFalse(Polyedr.is_good_point(R3(0.0, 0.0, 0.0)))
        self.assertFalse(Polyedr.is_good_point(R3(0.5, 0.5, 0.5)))  # на границе малого

    def test_outside_large_cube(self):
        """Точка вне большого куба — не «хорошая»"""
        self.assertFalse(Polyedr.is_good_point(R3(1.5, 0.0, 0.0)))
        self.assertFalse(Polyedr.is_good_point(R3(0.0, 1.2, 0.0)))
        self.assertFalse(Polyedr.is_good_point(R3(0.0, 0.0, -1.1)))
        self.assertFalse(Polyedr.is_good_point(R3(2.0, 2.0, 2.0)))

    def test_on_boundary_large_cube(self):
        """Точка на границе большого куба — не «хорошая» (строго внутри)"""
        self.assertFalse(Polyedr.is_good_point(R3(1.0, 0.0, 0.0)))
        self.assertFalse(Polyedr.is_good_point(R3(0.0, -1.0, 0.0)))
        self.assertFalse(Polyedr.is_good_point(R3(0.0, 0.0, 1.0)))

    def test_on_boundary_small_cube(self):
        """Точка на границе малого куба — не «хорошая» (строго вне)"""
        self.assertFalse(Polyedr.is_good_point(R3(0.5, 0.0, 0.0)))
        self.assertFalse(Polyedr.is_good_point(R3(-0.5, 0.3, 0.4)))
        self.assertFalse(Polyedr.is_good_point(R3(0.2, 0.5, 0.2)))


class TestProjectionAreaXY(unittest.TestCase):
    """Тесты для метода Facet.projection_area_xy (работает с УЖЕ трансформированными вершинами)"""

    def test_square_in_xy_plane(self):
        f = Facet([R3(0.0, 0.0, 0.0), R3(2.0, 0.0, 0.0), R3(2.0, 2.0, 0.0), R3(0.0, 2.0, 0.0)])
        self.assertAlmostEqual(f.projection_area_xy(), 4.0, places=6)

    def test_triangle_in_xy_plane(self):
        f = Facet([R3(0.0, 0.0, 0.0), R3(3.0, 0.0, 0.0), R3(0.0, 4.0, 0.0)])
        self.assertAlmostEqual(f.projection_area_xy(), 6.0, places=6)

    def test_tilted_facet(self):
        f = Facet([R3(0.0, 0.0, 0.0), R3(2.0, 0.0, 1.0), R3(0.0, 2.0, 1.0)])
        self.assertAlmostEqual(f.projection_area_xy(), 2.0, places=6)

    def test_vertical_facet_projection(self):
        f = Facet([R3(0.0, 1.0, 0.0), R3(2.0, 1.0, 0.0), R3(2.0, 3.0, 0.0), R3(0.0, 3.0, 0.0)])
        self.assertAlmostEqual(f.projection_area_xy(), 4.0, places=6)

    def test_degenerate_facet(self):
        f2 = Facet([R3(0.0, 0.0, 0.0), R3(1.0, 1.0, 0.0)])
        self.assertEqual(f2.projection_area_xy(), 0.0)
        f1 = Facet([R3(0.0, 0.0, 0.0)])
        self.assertEqual(f1.projection_area_xy(), 0.0)

    def test_concave_polygon_projection(self):
        f = Facet([R3(0.0, 0.0, 0.0), R3(2.0, 1.0, 0.0), R3(0.0, 2.0, 0.0), R3(1.0, 1.0, 0.0)])
        self.assertAlmostEqual(f.projection_area_xy(), 1.0, places=6)


class TestSumProjectionAreasGoodVertices(unittest.TestCase):
    """
    Тесты для sum_projection_areas_good_vertices.
    Ключевой момент: флаг _is_good вычисляется по ИСХОДНЫМ координатам,
    но площадь проекции считается по ТРАНСФОРМИРОВАННЫМ вершинам.
    """

    def test_all_vertices_good_no_transform(self):
        """Все вершины «хорошие», без трансформаций (c=1, углы=0)"""
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
        tmp = _make_temp_geom(fake_geom)
        try:
            poly = Polyedr(tmp)
            # Все 8 вершин: |±0.75| < 1 и > 0.5 → все «хорошие»
            
            # Проекция на плоскость XY:
            # - 2 горизонтальные грани (верх/низ): площадь проекции = 1.5×1.5 = 2.25 каждая
            # - 4 вертикальные грани: проецируются в отрезки → площадь = 0
            # Итого: 2.25 + 2.25 = 4.5
            result = poly.sum_projection_areas_good_vertices()
            self.assertAlmostEqual(result, 4.5, places=6)
            
            # Дополнительно: проверяем, что флаг установлен корректно
            for v in poly.vertexes:
                self.assertTrue(getattr(v, '_is_good', False), "Вершина должна быть помечена как хорошая")
        finally:
            os.unlink(tmp)

    def test_mixed_good_bad_no_transform(self):
        """Смешанные вершины, без трансформаций"""
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
            
            # Проверка флагов по исходным координатам:
            # (0.75,0,0) → хорошая, (0,0.75,0) → хорошая, (0.25,0.25,0.25) → плохая, (1.5,0,0) → плохая
            self.assertTrue(poly.vertexes[0]._is_good)
            self.assertTrue(poly.vertexes[1]._is_good)
            self.assertFalse(poly.vertexes[2]._is_good)
            self.assertFalse(poly.vertexes[3]._is_good)
            
            # Все 4 грани содержат хотя бы одну хорошую вершину → суммируем все проекции
            result = poly.sum_projection_areas_good_vertices()
            self.assertGreater(result, 0.0)
            self.assertTrue(isclose(result, result))  # не NaN
        finally:
            os.unlink(tmp)

    def test_no_good_vertices(self):
        """Ни одна вершина не «хорошая» → сумма = 0"""
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
            
            # Проверка: все флаги должны быть False
            for v in poly.vertexes:
                self.assertFalse(getattr(v, '_is_good', False))
        finally:
            os.unlink(tmp)

    def test_good_flag_uses_raw_coords_with_scaling(self):
        """
        Критический тест: флаг вычисляется по ИСХОДНЫМ координатам,
        даже если после масштабирования точка выходит за пределы кубов.
        """
        # Исходная вершина (0.75, 0, 0) — хорошая (|0.75| < 1 и > 0.5)
        # После масштабирования c=10: (7.5, 0, 0) — уже вне большого куба
        # Но флаг должен остаться True, т.к. проверка была на исходных координатах
        fake_geom = """10.0 0.0 0.0 0.0
1 1 0
0.75 0.0 0.0
1 1"""
        tmp = _make_temp_geom(fake_geom)
        try:
            poly = Polyedr(tmp)
            # Проверяем, что флаг установлен по исходным координатам
            self.assertTrue(poly.vertexes[0]._is_good, "Флаг должен быть основан на исходных координатах")
            
            # После масштабирования координата должна быть ~7.5
            self.assertAlmostEqual(poly.vertexes[0].x, 7.5, places=6)
        finally:
            os.unlink(tmp)

    def test_good_flag_uses_raw_coords_with_rotation(self):
        """
        Тест: флаг не зависит от поворотов.
        Исходная (0.75, 0, 0) — хорошая. После поворота на 90° вокруг Z: (0, 0.75, 0) — тоже хорошая,
        но флаг должен быть установлен ДО поворота.
        """
        fake_geom = """1.0 0.0 0.0 90.0
1 1 0
0.75 0.0 0.0
1 1"""
        tmp = _make_temp_geom(fake_geom)
        try:
            poly = Polyedr(tmp)
            # Флаг должен быть установлен по исходным (0.75, 0, 0)
            self.assertTrue(poly.vertexes[0]._is_good)
            
            # После поворота на 90° вокруг Z: (0.75, 0, 0) → (0, 0.75, 0)
            # Проверяем, что координаты изменились, но флаг остался от исходных
            self.assertAlmostEqual(poly.vertexes[0].x, 0.0, places=6)
            self.assertAlmostEqual(poly.vertexes[0].y, 0.75, places=6)
        finally:
            os.unlink(tmp)

    def test_projection_uses_transformed_coords(self):
        """
        Тест: площадь проекции считается по ТРАНСФОРМИРОВАННЫМ вершинам.
        Исходный квадрат 1×1 в плоскости XY, масштаб c=2 → проекция должна быть 4.0
        """
        fake_geom = """2.0 0.0 0.0 0.0
4 1 4
0.0 0.0 0.0
1.0 0.0 0.0
1.0 1.0 0.0
0.0 1.0 0.0
4 1 2 3 4"""
        tmp = _make_temp_geom(fake_geom)
        try:
            poly = Polyedr(tmp)
            
            # Все вершины: (0,0,0) — плохая, остальные — хорошие (|1.0| не < 1, но |1.0| == 1 → не строго внутри!)
            # На самом деле: (1.0, *, *) не проходит проверку |x| < 1 → все вершины плохие
            # Исправим: возьмём (0.75, 0.75, 0) и т.д.
        finally:
            os.unlink(tmp)
        
        # Пересоздаём с корректными «хорошими» вершинами
        fake_geom = """2.0 0.0 0.0 0.0
4 1 4
0.75 0.75 0.0
0.75 -0.75 0.0
-0.75 -0.75 0.0
-0.75 0.75 0.0
4 1 2 3 4"""
        tmp = _make_temp_geom(fake_geom)
        try:
            poly = Polyedr(tmp)
            
            # Все 4 вершины: |±0.75| < 1 и > 0.5 → все хорошие
            # Исходный квадрат 1.5×1.5, после масштабирования c=2 → 3.0×3.0
            # Площадь проекции на XY: 9.0
            result = poly.sum_projection_areas_good_vertices()
            self.assertAlmostEqual(result, 9.0, places=6)
        finally:
            os.unlink(tmp)


class TestBackwardCompatibility(unittest.TestCase):
    """Проверка, что нововведения не ломают существующий функционал"""

    def test_polyedr_init_unchanged(self):
        """Конструктор Polyedr работает как прежде (с добавлением флага _is_good)"""
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
            # Новый атрибут не должен ломать старые методы
            self.assertTrue(hasattr(poly.vertexes[0], '_is_good'))
        finally:
            os.unlink(tmp)

    def test_facet_methods_unchanged(self):
        """Методы Facet работают как прежде"""
        f = Facet([R3(0.0, 0.0, 0.0), R3(3.0, 0.0, 0.0), R3(0.0, 3.0, 0.0)])
        self.assertFalse(f.is_vertical())
        self.assertIsNotNone(f.h_normal())
        self.assertEqual(len(f.v_normals()), 3)
        self.assertIsInstance(f.center(), R3)
        area = f.projection_area_xy()
        self.assertIsInstance(area, float)
        self.assertGreater(area, 0.0)

    def test_edge_class_unchanged(self):
        """Класс Edge не затронут изменениями"""
        from shadow.polyedr import Edge
        e = Edge(R3(0.0, 0.0, 0.0), R3(1.0, 1.0, 1.0))
        self.assertEqual(len(e.gaps), 1)
        self.assertFalse(e.gaps[0].is_degenerate())
        f = Facet([R3(0.0, 0.0, 2.0), R3(2.0, 0.0, 2.0), R3(0.0, 2.0, 2.0)])
        e.shadow(f)
