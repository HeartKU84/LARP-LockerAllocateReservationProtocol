import socket

HOST = "0.0.0.0"
PORT = 5000
TIMEOUT = 60

DELIMITER = b"\r\n\r\n"

# Locker Database (Hardcode)
lockers = {
    "L01": {"status": "AVAILABLE", "owner": None},
    "L02": {"status": "AVAILABLE", "owner": None},
    "L03": {"status": "AVAILABLE", "owner": None},
    "L04": {"status": "AVAILABLE", "owner": None},
    "L05": {"status": "AVAILABLE", "owner": None},
}

# -----------------------------

# Receive one LARP message
def receive_message(conn):
    data = b""

    while DELIMITER not in data:
        chunk = conn.recv(1024)

        if not chunk:
            return None

        data += chunk

    message = data.split(DELIMITER, 1)[0]

    return message.decode("utf-8")

# -----------------------------

# Send LARP response
def send_message(conn, message):
    full_message = message + "\r\n\r\n"

    print("\n========== SERVER SEND ==========")
    print(message)
    print("=================================\n")

    conn.sendall(full_message.encode("utf-8"))

# -----------------------------

# Parse Headers
def parse_message(message):
    lines = message.split("\r\n")

    request_line = lines[0]
    headers = {}

    for line in lines[1:]:

        if ":" not in line:
            return request_line, None

        key, value = line.split(":", 1)

        headers[key.strip()] = value.strip()

    return request_line, headers

# -----------------------------

# LIST
def handle_list(parts, headers):

    # LIST <TYPE> LARP/1.0
    if len(parts) != 3:
        return "LARP/1.0 400 BAD REQUEST"

    list_type = parts[1]
    version = parts[2]

    if version != "LARP/1.0":
        return "LARP/1.0 400 BAD REQUEST"

    result = []

    # LIST ALL
    if list_type == "ALL":

        if headers:
            return "LARP/1.0 400 BAD REQUEST"

        for locker_id, locker in lockers.items():
            result.append(
                f"{locker_id} {locker['status']}"
            )

    # LIST AVAILABLE
    elif list_type == "AVAILABLE":

        if headers:
            return "LARP/1.0 400 BAD REQUEST"

        for locker_id, locker in lockers.items():

            if locker["status"] == "AVAILABLE":
                result.append(
                    f"{locker_id} AVAILABLE"
                )

    # LIST RESERVED
    elif list_type == "RESERVED":

        if headers:
            return "LARP/1.0 400 BAD REQUEST"

        for locker_id, locker in lockers.items():

            if locker["status"] == "RESERVED":
                result.append(
                    f"{locker_id} RESERVED"
                )

    # LIST MINE
    elif list_type == "MINE":

        if set(headers.keys()) != {"User-ID"}:
            return "LARP/1.0 400 BAD REQUEST"

        user_id = headers["User-ID"]

        for locker_id, locker in lockers.items():

            if (
                locker["status"] == "RESERVED"
                and locker["owner"] == user_id
            ):
                result.append(
                    f"{locker_id} RESERVED"
                )

        if len(result) == 0:
            return "LARP/1.0 404 RESERVATION NOT FOUND"

    else:
        return "LARP/1.0 400 BAD REQUEST"

    response = (
        "LARP/1.0 200 OK\r\n"
        f"Count: {len(result)}"
    )

    if result:
        response += "\r\n" + "\r\n".join(result)

    return response

# -----------------------------

# STATUS
def handle_status(parts, headers):

    # STATUS L03 LARP/1.0
    if len(parts) != 3:
        return "LARP/1.0 400 BAD REQUEST"

    if headers:
        return "LARP/1.0 400 BAD REQUEST"

    locker_id = parts[1]
    version = parts[2]

    if version != "LARP/1.0":
        return "LARP/1.0 400 BAD REQUEST"

    if locker_id not in lockers:
        return "LARP/1.0 404 LOCKER NOT FOUND"

    locker = lockers[locker_id]

    # ไม่ส่ง Owner/User-ID เพื่อรักษาความเป็นส่วนตัว
    return (
        "LARP/1.0 200 OK\r\n"
        f"Locker-ID: {locker_id}\r\n"
        f"Status: {locker['status']}"
    )

# -----------------------------

# RESERVE
def handle_reserve(parts, headers):

    # RESERVE L03 LARP/1.0
    if len(parts) != 3:
        return "LARP/1.0 400 BAD REQUEST"

    locker_id = parts[1]
    version = parts[2]

    if version != "LARP/1.0":
        return "LARP/1.0 400 BAD REQUEST"

    if set(headers.keys()) != {"User-ID"}:
        return "LARP/1.0 400 BAD REQUEST"

    user_id = headers["User-ID"]

    if not user_id:
        return "LARP/1.0 400 BAD REQUEST"

    if locker_id not in lockers:
        return "LARP/1.0 404 LOCKER NOT FOUND"

    locker = lockers[locker_id]

    if locker["status"] == "RESERVED":

        if locker["owner"] == user_id:
            return (
                "LARP/1.0 201 ALREADY RESERVED\r\n"
                f"Locker-ID: {locker_id}"
            )

        return "LARP/1.0 409 LOCKER OCCUPIED"

    # AVAILABLE -> RESERVED
    locker["status"] = "RESERVED"
    locker["owner"] = user_id

    return (
        "LARP/1.0 201 RESERVED\r\n"
        f"Locker-ID: {locker_id}\r\n"
        f"User-ID: {user_id}"
    )

# -----------------------------

# RELEASE
def handle_release(parts, headers):

    # RELEASE L03 LARP/1.0
    if len(parts) != 3:
        return "LARP/1.0 400 BAD REQUEST"

    locker_id = parts[1]
    version = parts[2]

    if version != "LARP/1.0":
        return "LARP/1.0 400 BAD REQUEST"

    if set(headers.keys()) != {"User-ID"}:
        return "LARP/1.0 400 BAD REQUEST"

    user_id = headers["User-ID"]

    if not user_id:
        return "LARP/1.0 400 BAD REQUEST"

    if locker_id not in lockers:
        return "LARP/1.0 404 LOCKER NOT FOUND"

    locker = lockers[locker_id]

    # Locker ยังไม่ได้ถูกจอง
    if locker["status"] == "AVAILABLE":
        return "LARP/1.0 409 NOT RESERVED"

    # Locker ถูกจอง แต่ไม่ใช่ Owner
    if locker["owner"] != user_id:
        return "LARP/1.0 403 NOT OWNER"

    # RESERVED -> AVAILABLE
    locker["status"] = "AVAILABLE"
    locker["owner"] = None

    return (
        "LARP/1.0 204 RELEASED\r\n"
        f"Locker-ID: {locker_id}"
    )

# -----------------------------

# Process Request
def process_request(message):

    request_line, headers = parse_message(message)

    if headers is None:
        return "LARP/1.0 400 BAD REQUEST", False

    parts = request_line.split()

    if len(parts) == 0:
        return "LARP/1.0 400 BAD REQUEST", False

    command = parts[0]

    if command == "LIST":
        return handle_list(parts, headers), False

    elif command == "STATUS":
        return handle_status(parts, headers), False

    elif command == "RESERVE":
        return handle_reserve(parts, headers), False

    elif command == "RELEASE":
        return handle_release(parts, headers), False

    elif command == "QUIT":

        if (
            len(parts) != 2
            or parts[1] != "LARP/1.0"
            or headers
        ):
            return "LARP/1.0 400 BAD REQUEST", False

        return "LARP/1.0 200 OK", True

    else:
        return "LARP/1.0 400 BAD REQUEST", False

# -----------------------------

# Main Server
def main():

    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server_socket.bind((HOST, PORT))

    server_socket.listen(5)

    print("=================================")
    print(" LARP/1.0 Server")
    print(" Locker Allocate Reservation Protocol")
    print("=================================")

    print(f"Server listening on port {PORT}")

    while True:

        print("\nWaiting for client...")

        conn, address = server_socket.accept()

        print(f"Client connected: {address}")

        # 60 seconds inactivity timeout
        conn.settimeout(TIMEOUT)

        try:

            while True:

                try:
                    message = receive_message(conn)

                except socket.timeout:

                    send_message(
                        conn,
                        "LARP/1.0 408 SESSION TIMEOUT"
                    )

                    print("Client session timeout.")
                    break

                if message is None:
                    print("Client disconnected.")
                    break

                print("\n========= SERVER RECEIVED =========")
                print(message)
                print("===================================\n")

                response, should_quit = process_request(
                    message
                )

                send_message(conn, response)

                if should_quit:
                    print("Client requested QUIT.")
                    break

        except ConnectionResetError:
            print("Client connection lost.")

        finally:
            conn.close()

            print("Connection closed.")


if __name__ == "__main__":
    main()