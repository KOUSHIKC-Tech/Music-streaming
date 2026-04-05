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
        # Send song list
        songs = os.listdir(SONG_DIR)
        song_list = ",".join(songs)
        client_socket.send(song_list.encode())

        # Receive selection
        song_name = client_socket.recv(1024).decode()
        file_path = os.path.join(SONG_DIR, song_name)

        if not os.path.exists(file_path):
            client_socket.sendall(b"ERROR\n")
            client_socket.close()
            return

        client_socket.sendall(b"OK\n")

        # Send file size
        file_size = os.path.getsize(file_path)
        client_socket.sendall(f"{file_size}\n".encode())

        # Calculate and send MD5 hash
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        client_socket.sendall(hash_md5.hexdigest().encode() + b"\n")

        # Send total number of packets
        BUFFER_SIZE = 4096
        total_packets = (file_size + BUFFER_SIZE - 1) // BUFFER_SIZE  # Ceiling division
        client_socket.sendall(f"{total_packets}\n".encode())

        start_time = time.time()
        total_sent = 0

        BUFFER_SIZE = 4096

        # Store packets for retransmission
        packets = {}
        seq_num = 0

        with open(file_path, 'rb') as f:
            while True:
                data = f.read(BUFFER_SIZE)
                if not data:
                    break

                # Simulate packet loss (10%)
                if random.random() < 0.1:
                    print(f"[{addr}] Packet {seq_num} lost (simulated)")
                    packets[seq_num] = data  # Store for retransmission
                    seq_num += 1
                    continue

                # Send sequence number + length + data
                packet = seq_num.to_bytes(4, 'big') + len(data).to_bytes(4, 'big') + data
                send_start = time.time()
                client_socket.sendall(packet)
                send_end = time.time()

                packets[seq_num] = data  # Store for retransmission
                total_sent += len(data)
                seq_num += 1

                # Adaptive buffer (simple logic)
                if (send_end - send_start) > 0.05:
                    BUFFER_SIZE = 1024
                else:
                    BUFFER_SIZE = 4096

        # Send end marker
        client_socket.sendall(END_MARKER)

        # Handle retransmission requests
        while True:
            try:
                client_socket.settimeout(5.0)  # Wait 5 seconds for retransmission requests
                request = client_socket.recv(1024).decode()
                if request.startswith("MISSING:"):
                    missing_packets = request[8:].split(",")
                    print(f"[{addr}] Retransmitting {len(missing_packets)} packets")
                    
                    for seq_str in missing_packets:
                        if seq_str:
                            seq = int(seq_str)
                            if seq in packets:
                                packet = seq.to_bytes(4, 'big') + len(packets[seq]).to_bytes(4, 'big') + packets[seq]
                                client_socket.sendall(packet)
                    
                    # Send end marker again
                    client_socket.sendall(END_MARKER)
                else:
                    break
            except socket.timeout:
                break

        end_time = time.time()

        # QoS Metrics
        total_time = end_time - start_time
        throughput = total_sent / total_time if total_time > 0 else 0

        print(f"[{addr}] Time: {total_time:.2f}s | Throughput: {throughput:.2f} bytes/sec")

    except Exception as e:
        print("Error:", e)

    client_socket.close()
    print(f"Disconnected: {addr}")


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"Server running on port {PORT}")

    while True:
        client_socket, addr = server.accept()

        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()


if __name__ == "__main__":
    start_server()