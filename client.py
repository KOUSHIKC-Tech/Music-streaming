import hashlib
import os
import socket
import subprocess

HOST = "127.0.0.1"
PORT = 5000
END_MARKER = b"END_OF_T"
BUFFER_SECONDS = 10
ESTIMATED_BYTES_PER_SECOND = 32000
BUFFER_START_BYTES = BUFFER_SECONDS * ESTIMATED_BYTES_PER_SECOND


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


def play_in_media_player(file_path):
    abs_path = os.path.abspath(file_path)
    wmplayer = r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe"
    if os.path.exists(wmplayer):
        subprocess.Popen([wmplayer, abs_path], creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        os.startfile(abs_path)


def open_downloaded_file(file_path):
    os.startfile(os.path.abspath(file_path))


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

songs = client.recv(4096).decode().split(",")

print("Available songs:")
for i, song in enumerate(songs):
    print(f"{i + 1}. {song}")

choice = int(input("Enter song number: ")) - 1
client.send(songs[choice].encode())

status = recv_line(client)

if status == "ERROR":
    print("Song not found")
else:
    expected_size = int(recv_line(client))
    expected_hash = recv_line(client)
    total_packets = int(recv_line(client))

    print(f"Streaming started ({expected_size} bytes)...")
    print(f"Expected MD5: {expected_hash}")
    print(f"Total packets expected: {total_packets}")

    stream_file = "stream.mp3"
    buffer_file = "stream_buffer.mp3"
    final_file = "received.mp3"

    if os.path.exists(stream_file):
        os.remove(stream_file)
    if os.path.exists(buffer_file):
        os.remove(buffer_file)

    f_stream = open(stream_file, "wb")
    f_buffer = open(buffer_file, "wb")

    received_packets = {}
    received_data = {}

    bytes_written = 0
    started = False
    initial_packets_received = 0
    retransmitted_packets_received = 0

    while True:
        header = recv_exact(client, 8)
        if not header:
            break
        if header == END_MARKER:
            break

        seq = int.from_bytes(header[:4], "big")
        length = int.from_bytes(header[4:], "big")
        data = recv_exact(client, length)

        received_packets[seq] = True
        received_data[seq] = data
        initial_packets_received += 1

        f_stream.write(data)
        f_stream.flush()

        f_buffer.write(data)
        f_buffer.flush()
        bytes_written += len(data)

        # Start the media player after buffering about 10 seconds of audio.
        if not started and bytes_written >= BUFFER_START_BYTES:
            try:
                print(
                    f"Buffered about {BUFFER_SECONDS} seconds. "
                    "Starting media player with buffer file..."
                )
                play_in_media_player(buffer_file)
                started = True
            except OSError:
                print("Could not start media player. Will open the finished song.")

    f_stream.close()
    f_buffer.close()
    print(f"Initial packets received: {initial_packets_received}")

    missing = [i for i in range(total_packets) if i not in received_packets]
    print(f"Missing packet count: {len(missing)}")
    if missing:
        print(f"Missing packet numbers: {missing}")

    if missing:
        client.sendall(("MISSING:" + ",".join(map(str, missing))).encode())
        print(f"Requested retransmission for {len(missing)} packets")

        while True:
            header = recv_exact(client, 8)
            if not header or header == END_MARKER:
                break

            seq = int.from_bytes(header[:4], "big")
            length = int.from_bytes(header[4:], "big")
            data = recv_exact(client, length)

            received_packets[seq] = True
            received_data[seq] = data
            retransmitted_packets_received += 1

    print(f"Retransmitted packets received: {retransmitted_packets_received}")

    with open(final_file, "wb") as f:
        for i in range(total_packets):
            if i in received_data:
                f.write(received_data[i])

    with open(final_file, "rb") as f:
        received_hash = hashlib.md5(f.read()).hexdigest()

    if received_hash == expected_hash:
        print(f"Received MD5: {received_hash}")
        print("Integrity OK")
        if not started:
            print("Opening downloaded song...")
            open_downloaded_file(final_file)
    else:
        print(f"Received MD5: {received_hash}")
        print("Corrupted file")

client.close()
