import numpy as np

from minpause.scenarios import generate_scenarios, latin_hypercube


def test_latin_hypercube_shape_and_bounds():
    design = latin_hypercube(20, 4, 7)
    assert design.shape == (20, 4)
    assert np.all((design >= 0) & (design < 1))


def test_latin_hypercube_has_one_point_per_stratum():
    design = latin_hypercube(25, 3, 9)
    for column in range(3):
        strata = np.floor(design[:, column] * 25).astype(int)
        assert sorted(strata) == list(range(25))


def test_scenario_generation_is_deterministic():
    first = generate_scenarios(5, seed=11)
    second = generate_scenarios(5, seed=11)
    assert first[0].price_shock == second[0].price_shock
    assert first[0].users[0] == second[0].users[0]


def test_full_design_contains_360_scenarios():
    assert len(generate_scenarios()) == 360


def test_recovery_actions_are_marked_critical():
    scenario = generate_scenarios(1)[0]
    protected = {op.name for op in scenario.operations if op.recovery_critical}
    assert protected == {"repay", "add_collateral"}

