import socket

def parse_ini(filename):
    config = {}
    with open(filename, 'r') as f:
        section = None
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
                config[section] = {}
            elif "=" in line and section:
                key, value = [item.strip() for item in line.split("=", 1)]
                config[section][key] = value
    return config

def update_ini(filename, updates):
    lines = []
    with open(filename, 'r') as f:
        lines = f.readlines()

    with open(filename, 'w') as f:
        section = None
        skip = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                section = stripped[1:-1]
                f.write(line)
                skip = False
            elif "=" in stripped and section and section in updates:
                key = stripped.split("=")[0].strip()
                if key in updates[section]:
                    # update the value
                    indent = line[:line.find(key)]
                    line = "{}{} = {}\n".format(indent, key, updates[section][key])
                    f.write(line)
                    skip = True  # mark that we've updated this key
                elif not skip:
                    f.write(line)
            else:
                if not skip:
                    f.write(line)


def parse_request(req):
    req_str = req.decode('utf-8')
    lines = req_str.split("\r\n")
    header = lines[0].split()
    method, path, protocol = header
    return method, path

def parse_lat_long(location):
    lat, long = location.strip('[]').split(',')
    return lat.strip(), long.strip()

def format_lat_long(lat, long):
    return '[{}, {}]'.format(lat, long)

def handle_request(client_socket):
    ini_data = parse_ini('wwvb.ini')  # Fetch the current .ini data for every request
    req = client_socket.recv(4096)
    method, path = parse_request(req)

    lat, long = parse_lat_long(ini_data['RADIO_LOC']['location'])

    if method == "GET" and path == "/":
        response = "HTTP/1.1 200 OK\r\n"
        response += "Content-Type: text/html\r\n\r\n"
        response += f"""
            <html>
                <body>
                    <h1>WWVB NTP Server Config</h1>
                    <form action="/" method="post">
                        Sync only at night (power or efficiency concern):
                        <select name="nighttime">
                            <option value="True" {'selected' if ini_data['WWVB']['nighttime'] == 'True' else ''}>True</option>
                            <option value="False" {'selected' if ini_data['WWVB']['nighttime'] == 'False' else ''}>False</option>
                        </select><br><br>

                        <h3>Time Delay Calculation (based off speed of light formula)</h3>
                        Latitude (RADIO_LOC):
                        <input type="text" name="latitude" value="{lat}"><br>
                        Longitude (RADIO_LOC):
                        <input type="text" name="longitude" value="{long}"><br><br>
                        Meters Above Sea Level:
                        <input type="text" name="masl" value="{ini_data['RADIO_LOC'].get('masl', '')}"><br><br>
                        Antenna To Use:
                        <select name="antenna">
                            <option value="" {'selected' if not ini_data['RADIO_LOC'].get('antenna', '') else ''}>BOTH (alternating)</option>
                            <option value="1" {'selected' if ini_data['RADIO_LOC'].get('antenna', '') == '1' else ''}>1</option>
                            <option value="2" {'selected' if ini_data['RADIO_LOC'].get('antenna', '') == '2' else ''}>2</option>
                        </select><br><br>

                        <input type="submit" value="Save">
                    </form>
                </body>
            </html>
        """
        client_socket.send(response.encode('utf-8'))
    elif method == "POST" and path == "/":
        content = req.decode('utf-8').split('\r\n\r\n', 1)[1]
        post_data = dict(item.split("=") for item in content.split("&"))

        formatted_location = format_lat_long(post_data.get('latitude', ''), post_data.get('longitude', ''))

        updates = {
            'WWVB': {
                'nighttime': post_data.get('nighttime', 'False')
            },
            'RADIO_LOC': {
                'location': formatted_location,
                'masl': post_data.get('masl', ''),
                'antenna': post_data.get('antenna', '')
            }
        }
        update_ini('wwvb.ini', updates)

        response = "HTTP/1.1 200 OK\r\n"
        response += "Content-Type: text/html\r\n\r\n"
        response += """
            <html>
                <body>
                    <h1>Saved successfully!</h1>
                    <a href="/">Go back</a>
                </body>
            </html>
        """
        client_socket.send(response.encode('utf-8'))

    else:
        response = "HTTP/1.1 404 Not Found\r\n\r\n"
        response += "Not Found"
        client_socket.send(response.encode('utf-8'))

    client_socket.close()

def start_server():
    ini_data = parse_ini('wwvb.ini')

    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Listening on', addr)

    while True:
        client_socket, addr = s.accept()
        print('Connection from', addr)
        handle_request(client_socket)

start_server()

