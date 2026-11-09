"""Deterministic Latin-hypercube scenario generation."""

from __future__ import annotations

import numpy as np

from .model import AttackPath, Operation, Scenario, UserPosition


OPERATION_NAMES = (
    "supply",
    "withdraw",
    "borrow",
    "repay",
    "add_collateral",
    "liquidate",
    "flash_loan",
    "swap",
    "oracle_update",
)

ATTACK_CATALOG = {
    "oracle": (
        AttackPath("flash-oracle-borrow", frozenset({"flash_loan", "swap", "oracle_update", "borrow"})),
        AttackPath("spot-liquidation", frozenset({"swap", "oracle_update", "liquidate"})),
        AttackPath("stale-price-drain", frozenset({"oracle_update", "borrow", "withdraw"})),
    ),
    "liquidity": (
        AttackPath("borrow-withdraw", frozenset({"borrow", "withdraw"})),
        AttackPath("flash-withdraw", frozenset({"flash_loan", "withdraw"})),
        AttackPath("liquidate-withdraw", frozenset({"liquidate", "withdraw"})),
    ),
    "accounting": (
        AttackPath("supply-borrow-withdraw", frozenset({"supply", "borrow", "withdraw"})),
        AttackPath("flash-accounting-withdraw", frozenset({"flash_loan", "supply", "withdraw"})),
        AttackPath("oracle-accounting-borrow", frozenset({"oracle_update", "supply", "borrow"})),
    ),
    "composite": (
        AttackPath("flash-oracle-borrow", frozenset({"flash_loan", "swap", "oracle_update", "borrow"})),
        AttackPath("spot-liquidation", frozenset({"swap", "oracle_update", "liquidate"})),
        AttackPath("borrow-withdraw", frozenset({"borrow", "withdraw"})),
        AttackPath("flash-withdraw", frozenset({"flash_loan", "withdraw"})),
        AttackPath("supply-borrow-withdraw", frozenset({"supply", "borrow", "withdraw"})),
    ),
}


def latin_hypercube(n: int, dimensions: int, seed: int) -> np.ndarray:
    """Generate a centered, jittered Latin hypercube without extra dependencies."""

    rng = np.random.default_rng(seed)
    result = np.empty((n, dimensions), dtype=float)
    for column in range(dimensions):
        result[:, column] = (rng.permutation(n) + rng.random(n)) / n
    return result


def _operation_set(row: np.ndarray, liquidity: float) -> tuple[Operation, ...]:
    base = {
        "supply": 0.16,
        "withdraw": 0.18,
        "borrow": 0.17,
        "repay": 0.11,
        "add_collateral": 0.08,
        "liquidate": 0.10,
        "flash_loan": 0.06,
        "swap": 0.11,
        "oracle_update": 0.03,
    }
    profiles = {
        "supply": (0.45, 0.35, 0.20),
        "withdraw": (0.28, 0.34, 0.38),
        "borrow": (0.35, 0.40, 0.25),
        "repay": (0.40, 0.38, 0.22),
        "add_collateral": (0.52, 0.34, 0.14),
        "liquidate": (0.05, 0.15, 0.80),
        "flash_loan": (0.02, 0.08, 0.90),
        "swap": (0.22, 0.33, 0.45),
        "oracle_update": (0.33, 0.34, 0.33),
    }
    skew = 0.55 + 0.9 * row[7]
    scale = liquidity / 100_000_000.0
    operations = []
    for index, name in enumerate(OPERATION_NAMES):
        jitter = 0.75 + 0.5 * ((row[index % len(row)] + index * 0.173) % 1.0)
        cost = base[name] * jitter * (0.75 + 0.25 * scale)
        retail, medium, whale = profiles[name]
        whale = whale**skew
        normalizer = retail + medium + whale
        group_costs = {
            "retail": cost * retail / normalizer,
            "medium": cost * medium / normalizer,
            "whale": cost * whale / normalizer,
        }
        operations.append(
            Operation(
                name,
                pause_cost=cost,
                group_costs=group_costs,
                recovery_critical=name in {"repay", "add_collateral"},
            )
        )
    return tuple(operations)


def _users(
    rng: np.random.Generator,
    n_users: int,
    price_shock: float,
    recovery_capacity: float,
) -> tuple[UserPosition, ...]:
    groups = rng.choice(("retail", "medium", "whale"), n_users, p=(0.62, 0.29, 0.09))
    debt = rng.lognormal(mean=9.0, sigma=1.15, size=n_users)
    initial_hf = rng.uniform(1.03, 1.85, size=n_users)
    threshold = rng.uniform(0.72, 0.86, size=n_users)
    collateral_before = initial_hf * debt / threshold
    collateral_after = collateral_before * (1.0 - price_shock)
    repay = debt * rng.uniform(0.0, recovery_capacity, size=n_users)
    extra = collateral_before * rng.uniform(0.0, recovery_capacity, size=n_users)
    return tuple(
        UserPosition(
            float(collateral_after[i]),
            float(debt[i]),
            float(threshold[i]),
            float(repay[i]),
            float(extra[i]),
            str(groups[i]),
        )
        for i in range(n_users)
    )


def generate_scenarios(n: int = 360, seed: int = 20261109) -> list[Scenario]:
    """Generate the full reproducible experiment design."""

    design = latin_hypercube(n, 10, seed)
    families = tuple(ATTACK_CATALOG)
    scenarios: list[Scenario] = []
    for i, row in enumerate(design):
        price_shock = 0.02 + 0.43 * row[0]
        utilization = 0.35 + 0.63 * row[1]
        delay = 1.0 + 89.0 * row[2]
        attack_loss = 250_000.0 * (80.0 ** row[3])
        liquidity = 1_000_000.0 * (100.0 ** row[4])
        n_users = int(120 + 480 * row[5])
        recovery_capacity = 0.04 + 0.46 * row[6]
        family = families[min(int(row[8] * len(families)), len(families) - 1)]
        operations = _operation_set(row, liquidity)
        rng = np.random.default_rng(seed + 7919 * (i + 1))
        users = _users(rng, n_users, price_shock, recovery_capacity)
        scenarios.append(
            Scenario(
                scenario_id=i + 1,
                incident_family=family,
                price_shock=float(price_shock),
                utilization=float(utilization),
                detection_delay_minutes=float(delay),
                attack_loss_potential=float(attack_loss),
                liquidity=float(liquidity),
                activity_skew=float(row[7]),
                recovery_capacity=float(recovery_capacity),
                operations=operations,
                attack_paths=ATTACK_CATALOG[family],
                users=users,
            )
        )
    return scenarios

