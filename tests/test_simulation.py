from minpause.scenarios import generate_scenarios
from minpause.simulation import baseline_policies, evaluate_policy, run_scenarios


def test_all_policy_metrics_are_bounded():
    scenario = generate_scenarios(1, seed=3)[0]
    for policy in baseline_policies(scenario):
        row = evaluate_policy(scenario, policy)
        for key in (
            "attack_prevention_rate",
            "blocked_legitimate_fraction",
            "availability",
            "recovery_coverage",
            "fairness_disparity",
        ):
            assert 0 <= row[key] <= 1


def test_global_freeze_blocks_all_paths_and_activity():
    scenario = generate_scenarios(1, seed=5)[0]
    global_policy = next(p for p in baseline_policies(scenario) if p.name == "Global freeze")
    row = evaluate_policy(scenario, global_policy)
    assert row["attack_prevention_rate"] == 1
    assert row["blocked_legitimate_fraction"] == 1


def test_no_intervention_has_zero_prevention():
    scenario = generate_scenarios(1, seed=6)[0]
    policy = next(p for p in baseline_policies(scenario) if p.name == "No intervention")
    row = evaluate_policy(scenario, policy)
    assert row["attack_prevention_rate"] == 0
    assert row["availability"] == 1


def test_minpause_preserves_recovery_functions():
    scenario = generate_scenarios(1, seed=8)[0]
    policy = next(p for p in baseline_policies(scenario) if p.name == "MinPause")
    assert "repay" not in policy.paused
    assert "add_collateral" not in policy.paused


def test_run_count_is_scenarios_times_policies():
    scenarios = generate_scenarios(3, seed=10)
    assert len(run_scenarios(scenarios)) == 15

