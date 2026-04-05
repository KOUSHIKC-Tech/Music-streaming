import socket
import os
import time
import hashlib

HOST = '127.0.0.1'
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

END_MARKER = b"END_OF_T"
END_MARKER_LEN = len(END_MARKER)


def recv_exact(sock, n):
    data = b""
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


def recv_line(sock):
    line = b""
    while True:
        char = sock.recv(1)
        if not char:
            return None
        if char == b"\n":
            break
        line += char
    return line.decode()


# Receive song list
song_list = client.recv(4096).decode()
songs = song_list.split(",")

print("Available songs:")
for i, song in enumerate(songs):
    print(f"{i+1}. {song}")

choice = int(input("Enter song number: ")) - 1
selected_song = songs[choice]

client.send(selected_song.encode())

status_line = recv_line(client)

if status_line == "ERROR":
    print("Song not found")
else:
    # Receive expected file size
    expected_size = int(recv_line(client))
    print(f"Expected file size: {expected_size} bytes")

    # Receive expected MD5 hash
    expected_hash = recv_line(client)
    print(f"Expected MD5 hash: {expected_hash}")

    # Receive total number of packets
    total_packets = int(recv_line(client))
    print(f"Total packets expected: {total_packets}")

    start_time = time.time()

    # Track received packets
    received_packets = {}
    received_data = {}

    while True:
        header = recv_exact(client, END_MARKER_LEN)
        if header is None:
            break
        if header == END_MARKER:
            break

        seq_num = int.from_bytes(header[:4], 'big')
        length = int.from_bytes(header[4:], 'big')
        data = recv_exact(client, length)
        if data is None:
            break

        received_packets[seq_num] = True
        received_data[seq_num] = data

    # Check for missing packets
    missing_packets = []
    for i in range(total_packets):
        if i not in received_packets:
            missing_packets.append(i)

    print(f"Initial transfer complete. Missing {len(missing_packets)} packets")

    # Request retransmission of missing packets
    if missing_packets:
        missing_str = ",".join(map(str, missing_packets))
        client.sendall(f"MISSING:{missing_str}".encode())
        
        # Receive retransmitted packets
        while True:
            header = recv_exact(client, END_MARKER_LEN)
            if header is None:
                break
            if header == END_MARKER:
                break

            seq_num = int.from_bytes(header[:4], 'big')
            length = int.from_bytes(header[4:], 'big')
            data = recv_exact(client, length)
            if data is None:
                break

            received_packets[seq_num] = True
            received_data[seq_num] = data

    # Reassemble file in correct order
    with open("received.mp3", "wb") as f:
        for i in range(total_packets):
            if i in received_data:
                f.write(received_data[i])

    end_time = time.time()

    # Verify file integrity
    received_size = os.path.getsize("received.mp3")
    received_hash = hashlib.md5(open("received.mp3", "rb").read()).hexdigest()

    print("Download complete")
    print("Time taken:", end_time - start_time)
    print(f"Received file size: {received_size} bytes")
    print(f"Received MD5 hash: {received_hash}")

    # Check for data loss/corruption
    if received_size != expected_size:
        print(f"⚠️  SIZE MISMATCH! Expected: {expected_size}, Received: {received_size}")
        print(f"Data loss: {expected_size - received_size} bytes missing")

    if received_hash != expected_hash:
        print(f"⚠️  HASH MISMATCH! File may be corrupted")
        print(f"Expected: {expected_hash}")
        print(f"Received: {received_hash}")
    else:
        print("✅ File integrity verified - no corruption detected")

    # Play (Windows) - only if file seems intact
    if received_size == expected_size and received_hash == expected_hash:
        os.system("start received.mp3")
    else:
        print("⚠️  Not playing file due to integrity issues")

client.close()