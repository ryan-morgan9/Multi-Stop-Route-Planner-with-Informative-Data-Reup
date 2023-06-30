from itertools import permutations


# Calculate the shortest route using distances
def bruteforce_tsp(distances, start):
    # Get index of all locations
    vertex = []
    for i in range(len(distances)):
        vertex.append(i)
        
    # Get all possible routes using indexes
    all_routes = permutations(vertex)
    # No shortest route to begin with
    shortest_route = None
    # Large distance so new shortest route can replace bigger distance
    shortest_distance = 1000000000000000000000000000000000.0

    # For every possible route
    for route in all_routes:
        # Only if starting from the specified starting location
        if route[0] == start:
            # Current distance of route
            cur_distance = 0
            # For each location in the route
            for i in range(1, len(route)):
                # Get and add up all the distances in the route
                cur_distance += distances[route[i-1]][route[i]]

            # If distance of the route is smaller than shortest_distance then replace as shortest route
            if cur_distance < shortest_distance:
                shortest_distance = cur_distance
                shortest_route = route

    # Return new shortest route and distance
    return shortest_route, shortest_distance
