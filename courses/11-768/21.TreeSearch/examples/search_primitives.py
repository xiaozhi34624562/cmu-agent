"""Deterministic arithmetic checks for the lecture guide, with no model or network calls."""

from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import product
import json
from math import sqrt


@dataclass(frozen=True)
class Edge:
    prior: float
    visits: int
    value_sum: float

    def score(self, parent_visits: int) -> float:
        mean = self.value_sum / self.visits if self.visits else 0.0
        return mean + self.prior * sqrt(parent_visits) / (1 + self.visits)

    def add_outcome(self, outcome: float) -> 'Edge':
        return replace(self, visits=self.visits + 1, value_sum=self.value_sum + outcome)


@dataclass(frozen=True)
class Flight:
    id: str
    dollars: int
    arrival_minutes: int


@dataclass(frozen=True)
class Hotel:
    id: str
    dollars: int
    free_cancellation: bool


def feasible_trips() -> list[tuple[str, str, int]]:
    """Enumerate the guide's fixed quotes, filtering constraints before ranking."""
    flights = [Flight('F1', 350, 18 * 60 + 10), Flight('F2', 420, 16 * 60 + 30),
               Flight('F3', 460, 15 * 60 + 45)]
    hotels = [Hotel('A', 250, False), Hotel('B', 300, True), Hotel('C', 420, True)]
    feasible = []
    for flight, hotel in product(flights, hotels):
        total = flight.dollars + hotel.dollars
        if flight.arrival_minutes < 17 * 60 and hotel.free_cancellation and total <= 750:
            feasible.append((flight.id, hotel.id, total))
    return feasible


def main() -> None:
    edges = {'A': Edge(0.60, 4, 2.40), 'B': Edge(0.25, 3, 1.20), 'C': Edge(0.15, 2, 1.10)}
    scores = {name: edge.score(parent_visits=9) for name, edge in edges.items()}
    chosen = max(scores, key=scores.__getitem__)
    updated = edges[chosen].add_outcome(0.30)
    game_of_24 = 6 / (1 - Fraction(3, 4))
    trips = feasible_trips()
    serial = 1 + sum([4, 3, 2]) + 2
    parallel = 1 + max([4, 3, 2]) + 2

    assert game_of_24 == 24
    assert chosen == 'A' and updated.visits == 5
    assert round(updated.value_sum / updated.visits, 2) == 0.54
    assert trips == [('F2', 'B', 720)]
    assert (serial, parallel) == (12, 7)
    print(json.dumps({
        'scope': 'deterministic examples with fixed inputs; no model calls, network, or timing measurements',
        'game_of_24': game_of_24.numerator,
        'puct_scores': {name: round(value, 4) for name, value in scores.items()},
        'selected_edge': chosen,
        'updated_edge': {'visits': updated.visits, 'mean': round(updated.value_sum / updated.visits, 2)},
        'feasible_trips': trips,
        'dag_illustrative_minutes': {'serial': serial, 'parallel_lower_bound': parallel},
    }, indent=2))


if __name__ == '__main__':
    main()
