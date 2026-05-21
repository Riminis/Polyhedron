#!/usr/bin/env -S python3 -B

from time import time
from common.tk_drawer import TkDrawer
from shadow.polyedr import Polyedr


tk = TkDrawer()
try:
    for name in ["ccc", "cube", "box", "king", "cow"]:
        print("=============================================================")
        print(f"Начало работы с полиэдром '{name}'")
        start_time = time()
        Polyedr(f"polyhedron/data/{name}.geom").draw(tk)

        polyedr = Polyedr(f"polyhedron/data/{name}.geom")
        polyedr.draw(tk)

        result = polyedr.sum_projection_areas_good_vertices()
        print(f'Сумма площадей проекций граней с "хорошими" вершинами: {result}')

        delta_time = time() - start_time
        print(f"Изображение полиэдра '{name}' заняло {delta_time} сек.")
        input("Hit 'Return' to continue -> ")
except (EOFError, KeyboardInterrupt):
    print("\nStop")
    tk.close()
