def poll_sensor(connection):
    while True:
        try:
            reading = connection.read()
            process(reading)
        except Exception:
            pass
