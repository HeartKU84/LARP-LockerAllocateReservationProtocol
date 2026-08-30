import socket

HOST = "127.0.0.1"
PORT = 5000

DELIMITER = b"\r\n\r\n"


def send_message(sock, message):

    full_message = message + "\r\n\r\n"

    print("\n========== CLIENT SEND ==========")
    print(message)
    print("=================================\n")

    sock.sendall(
        full_message.encode("utf-8")
    )


def receive_message(sock):

    data = b""

    while DELIMITER not in data:

        chunk = sock.recv(1024)

        if not chunk:
            return None

        data += chunk

    message = data.split(
        DELIMITER,
        1
    )[0]

    return message.decode("utf-8")


def print_menu():

    print("\n========== LARP CLIENT ==========")
    print("1. LIST")
    print("2. STATUS")
    print("3. RESERVE")
    print("4. RELEASE")
    print("5. QUIT")
    print("=================================")


def list_menu(user_id):

    print("\nLIST TYPE")
    print("1. ALL")
    print("2. AVAILABLE")
    print("3. RESERVED")
    print("4. MINE")

    choice = input("Select: ")

    if choice == "1":

        return "LIST ALL LARP/1.0"

    elif choice == "2":

        return "LIST AVAILABLE LARP/1.0"

    elif choice == "3":

        return "LIST RESERVED LARP/1.0"

    elif choice == "4":

        return (
            "LIST MINE LARP/1.0\r\n"
            f"User-ID: {user_id}"
        )

    else:
        print("Invalid selection.")
        return None


def main():

    print("=================================")
    print(" LARP/1.0 Client")
    print(" Locker Allocate Reservation Protocol")
    print("=================================")

    user_id = input("Enter User-ID: ").strip()

    if not user_id:
        print("User-ID cannot be empty.")
        return

    client_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:

        client_socket.connect(
            (HOST, PORT)
        )

        print(
            f"\nConnected to LARP Server "
            f"{HOST}:{PORT}"
        )

        while True:

            print_menu()

            choice = input("Select: ").strip()

            request = None

            # LIST
            if choice == "1":

                request = list_menu(user_id)

            # STATUS
            elif choice == "2":

                locker_id = input(
                    "Locker-ID: "
                ).strip().upper()

                request = (
                    f"STATUS {locker_id} LARP/1.0"
                )

            # RESERVE
            elif choice == "3":

                locker_id = input(
                    "Locker-ID: "
                ).strip().upper()

                request = (
                    f"RESERVE {locker_id} LARP/1.0\r\n"
                    f"User-ID: {user_id}"
                )

            # RELEASE
            elif choice == "4":

                locker_id = input(
                    "Locker-ID: "
                ).strip().upper()

                request = (
                    f"RELEASE {locker_id} LARP/1.0\r\n"
                    f"User-ID: {user_id}"
                )

            # QUIT
            elif choice == "5":

                request = "QUIT LARP/1.0"

            else:

                print("Invalid selection.")
                continue

            if request is None:
                continue

            send_message(
                client_socket,
                request
            )

            response = receive_message(
                client_socket
            )

            if response is None:
                print("Server disconnected.")
                break

            print("\n--------- CLIENT RECEIVED ---------")
            print(response)
            print("-------------------------------------\n")

            if choice == "5":
                break

    except ConnectionRefusedError:

        print(
            "Cannot connect to server. "
            "Make sure server.py is running."
        )

    except ConnectionResetError:

        print("Connection lost.")

    finally:

        client_socket.close()

        print("Connection closed.")


if __name__ == "__main__":
    main()