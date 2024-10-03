from math import radians, sin, cos, sqrt, atan2
import networkx as nx

def extract_numeric_value(value_str):
    """
    Extracts the numeric value from a string containing numeric value followed by units.
    Example: "20km/h" -> 20
    """
    numeric_part = ""
    for char in value_str:
        if char.isdigit() or char == ".":
            numeric_part += char
        else:
            break
    return float(numeric_part) if numeric_part else None


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on the Earth's surface
    using the Haversine formula.

    Parameters:
    lat1 (float): Latitude of the first point in degrees.
    lon1 (float): Longitude of the first point in degrees.
    lat2 (float): Latitude of the second point in degrees.
    lon2 (float): Longitude of the second point in degrees.

    Returns:
    float: Distance between the two points in kilometers.
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    radius_earth = 6371  # Radius of the Earth in kilometers
    distance = radius_earth * c

    return distance


def calculate_angle(pos1, pos2):
    """
    Calculate the angle between two points.
    """
    lat1, lon1 = pos1
    lat2, lon2 = pos2
    return atan2(lat2 - lat1, lon2 - lon1)


def assign_orders_to_drone(orders, drone_capacity, drone_autonomy, center_location):
    orders_sorted_by_weight = sorted(
        orders, key=lambda x: x.weight, reverse=True)
    orders_with_ratios = []

    for order in orders_sorted_by_weight:
        distance_to_center = haversine_distance(
            center_location[0], center_location[1], order.latitude, order.longitude)
        weight_to_distance_ratio = order.weight * \
            distance_to_center if distance_to_center != 0 else float('inf')
        orders_with_ratios.append((order, weight_to_distance_ratio))

    # Sort orders by weight-to-distance ratio in ascending order
    orders_with_ratios.sort(key=lambda x: (x[0].weight, x[1]))

    assigned_orders = []
    current_capacity = 0
    current_autonomy = 0

    for order, _ in orders_with_ratios:
        if current_capacity + order.weight <= drone_capacity:
            if current_autonomy == 0:
                distance = haversine_distance(center_location[0], center_location[1], order.latitude, order.longitude)
                if current_autonomy + 2 * distance <= drone_autonomy:
                    assigned_orders.append(order)
                    current_capacity += order.weight
                    current_autonomy += distance
            else:
                distance2 = haversine_distance(assigned_orders[-1].latitude, assigned_orders[-1].longitude, order.latitude, order.longitude)
                if current_autonomy + distance2 + distance <= drone_autonomy:
                    assigned_orders.append(order)
                    current_capacity += order.weight
                    current_autonomy += distance2
        else:
            break  # Stop assigning orders if drone's capacity is reached

    return assigned_orders


def evaluate_proposals(proposals):
    best_proposal = None
    max_orders = 0
    max_weight = 0
    for proposal in proposals:
        #print(proposal)
        center_id, orders_dict = proposal
        orders = orders_dict["orders"]
        if orders != []:
            center_location = orders_dict["center"]
            orders, total_distance = sort_orders_by_shortest_path(orders, center_location)
            #print(f"Center {center_id}: {len(orders)} orders, {total_distance} km")
            num_orders = len(orders)
            total_weight = 0
            for order in orders:
                total_weight += order[3]

            if num_orders > max_orders or (num_orders == max_orders and total_weight > max_weight):
                max_orders = num_orders
                max_weight = total_weight
                best_proposal = (center_id, orders, center_location)
        

    return best_proposal


# orders = [order1, order2, order3, ...]
# center_location = (latitude, longitude)
def sort_orders_by_shortest_path(orders, center_location):
    G = nx.Graph()
    G.add_node('center', location=center_location)

    order_locations = []
    for order in orders:
        order_location = (order["id"], order["latitude"], order["longitude"], order["weight"])
        order_locations.append(order_location)
        G.add_node(order["id"], location=(order_location[1], order_location[2]))

    for order in order_locations:
        G.add_edge('center', order[0], weight=haversine_distance(
            center_location["latitude"], center_location["longitude"], order[1], order[2]))

    for i in range(len(order_locations)):
        for j in range(i + 1, len(order_locations)):
            distance = haversine_distance(
                order_locations[i][1], order_locations[i][2],
                order_locations[j][1], order_locations[j][2]
            )
            G.add_edge(order_locations[i][0], order_locations[j][0], weight=distance)

    tsp_path = nx.approximation.traveling_salesman_problem(G, cycle=True)

    if tsp_path is None: return [], float('inf')
    
    sorted_orders = []
    for i in tsp_path[1:-1]:
        sorted_orders.append([order_location for order_location in order_locations if order_location[0] == i][0])
    total_distance = sum(G[tsp_path[i-1]][tsp_path[i]]['weight'] for i in range(1,len(tsp_path)))

    return sorted_orders, total_distance

