def poll_sensor(connection, max_retries=3):
    for attempt in range(max_retries):
        try:
            return connection.read()
        except ConnectionError:
            continue
    return None
