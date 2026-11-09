"""Core data structures used by the optimizer and simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class Operation:
    """A pausable protocol action and its legitimate-use cost."""

    name: str
    pause_cost: float
    group_costs: Mapping[str, float] = field(default_factory=dict)
    recovery_critical: bool = False


@dataclass(frozen=True)
class AttackPath:
    """A set of actions that jointly form one executable loss path."""

    name: str
    operations: frozenset[str]
    probability: float = 1.0


@dataclass(frozen=True)
class UserPosition:
    """Simplified borrower state after the exogenous price shock."""

    collateral_value: float
    debt_value: float
    liquidation_threshold: float
    available_repayment: float
    available_extra_collateral: float
    group: str

    @property
    def health_factor(self) -> float:
        if self.debt_value <= 0:
            return float("inf")
        return self.collateral_value * self.liquidation_threshold / self.debt_value


@dataclass(frozen=True)
class Scenario:
    """One deterministic experiment configuration."""

    scenario_id: int
    incident_family: str
    price_shock: float
    utilization: float
    detection_delay_minutes: float
    attack_loss_potential: float
    liquidity: float
    activity_skew: float
    recovery_capacity: float
    operations: tuple[Operation, ...]
    attack_paths: tuple[AttackPath, ...]
    users: tuple[UserPosition, ...]


@dataclass(frozen=True)
class PausePolicy:
    """Result returned by the policy synthesizer."""

    name: str
    paused: frozenset[str]
    feasible: bool
    objective: float
    pause_cost: float
    fairness_disparity: float

