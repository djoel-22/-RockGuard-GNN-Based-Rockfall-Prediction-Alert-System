# nodeconnection.py
# Graph-based node connection and propagation logic for SimulationPage
# ===================================================================

from collections import deque
import math


class Node:
    """
    Represents a single stress node with sensor values.
    Each node stores its own ID, position (3D), and sensor readings.
    """
    def __init__(self, node_id, position, sensors=None):
        self.id = node_id
        self.position = position  # (x, y, z)
        self.sensors = sensors or {}  # {sensor_name: value}

    def set_sensor(self, key, value):
        self.sensors[key] = value

    def get_sensor(self, key, default=0.0):
        return self.sensors.get(key, default)


class NodeConnection:
    """
    Graph manager that stores connections and handles propagation.
    """
    def __init__(self, decay=0.7):
        # adjacency list: node_id -> set(neighbor_ids)
        self.connections = {}
        # node dictionary: node_id -> Node
        self.nodes = {}
        self.decay = decay

    # ---------------- Graph Setup ----------------
    def add_node(self, node: Node):
        self.nodes[node.id] = node
        if node.id not in self.connections:
            self.connections[node.id] = set()

    def add_connection(self, a_id, b_id):
        """Add bidirectional connection between two nodes"""
        if a_id not in self.nodes or b_id not in self.nodes:
            raise ValueError("Both nodes must exist before connecting")
        self.connections.setdefault(a_id, set()).add(b_id)
        self.connections.setdefault(b_id, set()).add(a_id)

    def get_neighbors(self, node_id):
        return list(self.connections.get(node_id, []))

    # ---------------- Propagation Logic ----------------
    def propagate_change(self, source_id, sensor_key, delta_value):
        """
        Spread a change in one sensor from a source node
        to all connected nodes with exponential decay.
        """
        if source_id not in self.nodes:
            raise ValueError("Source node does not exist")

        visited = set()
        queue = deque([(source_id, 0, delta_value)])  # (node_id, distance, delta)

        while queue:
            node_id, dist, effect = queue.popleft()
            if node_id in visited:
                continue
            visited.add(node_id)

            # Apply effect to node's sensor
            node = self.nodes[node_id]
            old_val = node.get_sensor(sensor_key, 0.0)
            node.set_sensor(sensor_key, old_val + effect)

            # Propagate to neighbors with decay
            for neighbor_id in self.get_neighbors(node_id):
                if neighbor_id not in visited:
                    weakened = delta_value * (self.decay ** (dist + 1))
                    if abs(weakened) > 1e-6:  # ignore tiny effects
                        queue.append((neighbor_id, dist + 1, weakened))

    # ---------------- Utility ----------------
    def reset_sensors(self, default_value=0.0):
        """Reset all sensor readings to a default"""
        for node in self.nodes.values():
            for key in node.sensors.keys():
                node.sensors[key] = default_value

    def distance(self, id1, id2):
        """Euclidean distance between two nodes (if positions are set)"""
        n1, n2 = self.nodes[id1], self.nodes[id2]
        p1, p2 = n1.position, n2.position
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))
