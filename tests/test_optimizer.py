from minpause.model import AttackPath, Operation
from minpause.optimizer import covers_all, synthesize_policy


def operation(name, cost, recovery=False):
    return Operation(name, cost, {"retail": cost / 2, "whale": cost / 2}, recovery)


def test_policy_covers_every_path():
    ops = (operation("a", 1), operation("b", 2), operation("c", 3))
    paths = (
        AttackPath("p1", frozenset({"a", "b"})),
        AttackPath("p2", frozenset({"b", "c"})),
    )
    policy = synthesize_policy(ops, paths, fairness_weight=0)
    assert policy.feasible
    assert covers_all(policy.paused, paths)


def test_optimizer_finds_minimum_cost_not_smallest_cardinality():
    ops = (operation("a", 2), operation("b", 2), operation("c", 5))
    paths = (
        AttackPath("p1", frozenset({"a", "c"})),
        AttackPath("p2", frozenset({"b", "c"})),
    )
    policy = synthesize_policy(ops, paths, fairness_weight=0)
    assert policy.paused == frozenset({"a", "b"})
    assert policy.pause_cost == 4


def test_recovery_operations_are_never_paused():
    ops = (operation("repay", 0.01, True), operation("borrow", 1.0))
    paths = (AttackPath("p", frozenset({"repay", "borrow"})),)
    policy = synthesize_policy(ops, paths)
    assert policy.paused == frozenset({"borrow"})


def test_infeasible_when_path_contains_only_recovery_operations():
    ops = (operation("repay", 0.01, True), operation("topup", 0.01, True))
    paths = (AttackPath("p", frozenset({"repay", "topup"})),)
    policy = synthesize_policy(ops, paths)
    assert not policy.feasible


def test_empty_attack_set_requires_no_pause():
    policy = synthesize_policy((operation("borrow", 1.0),), ())
    assert policy.feasible
    assert policy.paused == frozenset()

