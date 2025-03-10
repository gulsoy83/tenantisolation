def conn_replica(connections):
    if "replica" in connections:
        cursor = connections["replica"].cursor()
    else:
        cursor = connections["default"].cursor()
    return cursor
