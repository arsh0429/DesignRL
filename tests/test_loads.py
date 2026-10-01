"""Check that applied floor gravity is counted once at each level."""

import pytest

from structural_design_env.graph import StructuralGraph
from structural_design_env.solver.load_generator import _compute_tributary_areas, generate_loads
from structural_design_env.tasks.task2_office import TASK2_CONFIG


def test_gravity_load_is_not_repeated_on_lower_floors():
    graph = StructuralGraph(floor_height_m=TASK2_CONFIG.floor_height_m)
    for floor in range(TASK2_CONFIG.n_floors):
        graph.place_column(5, 5, floor, "HEB200")

    loads = generate_loads(graph, TASK2_CONFIG)
    floor_forces = [loads[f"n_5_5_{floor}"]["Fz"] for floor in range(1, 4)]
    assert floor_forces[0] == pytest.approx(floor_forces[1])
    assert floor_forces[1] == pytest.approx(floor_forces[2])
    assert floor_forces[0] == pytest.approx(-400 * (TASK2_CONFIG.dead_load_kPa + TASK2_CONFIG.live_load_kPa) * 1000)


def test_tributary_areas_cover_the_site_once():
    graph = StructuralGraph()
    graph.place_column(0, 0, 0, "HEB200")
    graph.place_column(5, 0, 0, "HEB200")
    areas = _compute_tributary_areas(graph, 20, 10)
    assert sum(areas.values()) == pytest.approx(200)
