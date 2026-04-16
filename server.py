import socket
import os
import threading
import time
import random
import hashlib

HOST = '0.0.0.0'
PORT = 5000
SONG_DIR = 'songs'
END_MARKER = b"END_OF_T"

def handle_client(client_socket, addr):
    print(f"Connected: {addr}")

    try:
        songs = os.listdir(SONG_DIR)
        client_socket.send(",".join(songs).encode())

        song_name = client_socket.recv(1024).decode()
        file_path = os.path.join(SONG_DIR, song_name)

        if not os.path.exists(file_path):
            client_socket.sendall(b"ERROR\n")
            return

        client_socket.sendall(b"OK\n")

        file_size = os.path.getsize(file_path)
        client_socket.sendall(f"{file_size}\n".encode())

        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        file_hash = hash_md5.hexdigest()
        client_socket.sendall(file_hash.encode() + b"\n")

        BUFFER_SIZE = 4096
        total_packets = (file_size + BUFFER_SIZE - 1) // BUFFER_SIZE
        client_socket.sendall(f"{total_packets}\n".encode())

        print(
            f"Streaming '{song_name}' | size={file_size} bytes | "
            f"packets={total_packets} | md5={file_hash}"
        )

        packets = {}
        seq_num = 0
        dropped_packets = []
        retransmission_count = 0

        with open(file_path, 'rb') as f:
            while True:
                data = f.read(BUFFER_SIZE)
                if not data:
                    break

                if random.random() < 0.1:
                    packets[seq_num] = data
                    dropped_packets.append(seq_num)
                    seq_num += 1
                    continue

                packet = seq_num.to_bytes(4, 'big') + len(data).to_bytes(4, 'big') + data
                client_socket.sendall(packet)

                time.sleep(0.01)  #  streaming delay

                packets[seq_num] = data
                seq_num += 1

        client_socket.sendall(END_MARKER)
        print(
            f"Initial send complete | intentionally dropped={len(dropped_packets)} "
            f"packets"
        )
        if dropped_packets:
            print(f"Dropped packet numbers: {dropped_packets}")

        while True:
            try:
                client_socket.settimeout(5.0)
                request = client_socket.recv(1024).decode()

                if request.startswith("MISSING:"):
                    missing_packets = request[8:].split(",")
                    missing_packets = [seq for seq in missing_packets if seq]
                    print(
                        f"Client reported {len(missing_packets)} missing packets: "
                        f"{missing_packets}"
                    )

                    for seq_str in missing_packets:
                        seq = int(seq_str)
                        if seq in packets:
                            packet = (
                                seq.to_bytes(4, 'big')
                                + len(packets[seq]).to_bytes(4, 'big')
                                + packets[seq]
                            )
                            client_socket.sendall(packet)
                            retransmission_count += 1
                            time.sleep(0.01)

                    client_socket.sendall(END_MARKER)
                    print(
                        f"Retransmission round complete | "
                        f"retransmitted={retransmission_count}"
                    )
                else:
                    break

            except socket.timeout:
                break

    except Exception as e:
        print("Error:", e)

    client_socket.close()
    print(f"Total retransmissions sent: {retransmission_count}")
    print(f"Disconnected: {addr}")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"Server running on port {PORT}")

    while True:
        client_socket, addr = server.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr)).start()

if __name__ == "__main__":
    start_server()
