import heapq
import itertools
import math

# Sample distances are demonstration data, not measured campus distances.
DEMO_CAMPUS_GRAPH = {
    "Library": {"Canteen": 450, "Block A": 250},
    "Canteen": {"Library": 450, "Block B": 300, "Parking": 500},
    "Block A": {"Library": 250, "Block B": 180, "Classroom": 90},
    "Block B": {"Canteen": 300, "Block A": 180, "Auditorium": 220},
    "Auditorium": {"Block B": 220, "Parking": 350},
    "Parking": {"Canteen": 500, "Auditorium": 350},
    "Classroom": {"Block A": 90},
}


def _normalize_location(value):
    if not isinstance(value, str):
        return ""
    return " ".join(
        "".join(character if character.isalnum() else " " for character in value.casefold()).split()
    )


def _validated_graph(graph):
    if not isinstance(graph, dict):
        raise ValueError("The route graph must be a node-to-neighbor mapping.")

    validated = {}
    nodes = set()
    for node, edges in graph.items():
        if not isinstance(node, str) or not node.strip() or not isinstance(edges, dict):
            raise ValueError("Each graph node must have a name and a neighbor mapping.")
        nodes.add(node)
        validated.setdefault(node, {})
        for neighbor, distance in edges.items():
            if not isinstance(neighbor, str) or not neighbor.strip():
                raise ValueError("Neighbor nodes must have non-empty names.")
            try:
                edge_cost = float(distance)
            except (TypeError, ValueError) as error:
                raise ValueError("Route distances must be finite non-negative numbers.") from error
            if not math.isfinite(edge_cost) or edge_cost < 0:
                raise ValueError("Route distances must be finite non-negative numbers.")
            nodes.add(neighbor)
            validated[node][neighbor] = edge_cost

    for node in nodes:
        validated.setdefault(node, {})
    return validated


def astar_search(graph, start, destination, heuristic=None):
    """Return the shortest path and distance using A*.

    ``graph`` maps each location to its neighboring locations and edge costs.
    A supplied heuristic must be admissible. With no reliable map geometry,
    the zero heuristic is used; this remains A* and guarantees an optimal route.
    """

    graph = _validated_graph(graph)
    if start not in graph:
        raise ValueError(f"Unknown starting location: {start}")
    if destination not in graph:
        raise ValueError(f"Unknown destination: {destination}")

    def estimate(node):
        if heuristic is None:
            return 0.0
        try:
            value = float(heuristic(node, destination))
        except (TypeError, ValueError) as error:
            raise ValueError("Heuristic values must be finite non-negative numbers.") from error
        if not math.isfinite(value) or value < 0:
            raise ValueError("Heuristic values must be finite non-negative numbers.")
        return value

    best_cost = {start: 0.0}
    parent = {}
    queue_order = itertools.count()
    frontier = [(estimate(start), next(queue_order), 0.0, start)]

    # The queue prioritizes the lowest estimated total cost f(n) = g(n) + h(n).
    while frontier:
        _, _, current_cost, current = heapq.heappop(frontier)
        if current_cost != best_cost.get(current):
            continue

        if current == destination:
            path = [destination]
            while path[-1] != start:
                path.append(parent[path[-1]])
            path.reverse()
            return {"path": path, "distance": current_cost}

        for neighbor, edge_cost in graph[current].items():
            candidate_cost = current_cost + edge_cost
            if candidate_cost < best_cost.get(neighbor, math.inf):
                best_cost[neighbor] = candidate_cost
                parent[neighbor] = current
                total_estimate = candidate_cost + estimate(neighbor)
                heapq.heappush(
                    frontier,
                    (total_estimate, next(queue_order), candidate_cost, neighbor),
                )

    return None


def map_report_location(location, graph=DEMO_CAMPUS_GRAPH, aliases=None):
    """Map a report location only when it exactly names a configured node."""

    normalized_location = _normalize_location(location)
    if not normalized_location:
        return None

    validated = _validated_graph(graph)
    for node in validated:
        if _normalize_location(node) == normalized_location:
            return node

    for alias, node in (aliases or {}).items():
        if _normalize_location(alias) == normalized_location and node in validated:
            return node
    return None