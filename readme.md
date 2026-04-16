# 🎵 Secure Audio Streaming System using Socket Programming

## 📌 Project Overview

This project implements a **secure client-server audio streaming system** using low-level socket programming. The system supports **multiple clients**, ensures **reliable data transmission**, and uses **SSL/TLS encryption** to secure all communication.

---

## 🎯 Objectives

* Stream audio files over a network
* Support multiple concurrent clients
* Ensure reliable transmission with packet recovery
* Secure communication using SSL/TLS
* Verify file integrity after transmission

---

## 🏗️ System Architecture

```
                    ┌────────────────────────────┐
                    │         SERVER             │
                    │  - Song Storage            │
                    │  - Packet Generator        │
                    │  - TLS Enabled             │
                    │  - Multi-threaded          │
                    └────────────┬───────────────┘
                                 │
                         TLS Secure Channel
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   CLIENT 1    │     │   CLIENT 2    │     │   CLIENT N    │
│ - Select song │     │ - Select song │     │ - Select song │
│ - Buffer data │     │ - Buffer data │     │ - Buffer data │
│ - Detect loss │     │ - Detect loss │     │ - Detect loss │
│ - Retransmit  │     │ - Retransmit  │     │ - Retransmit  │
└───────────────┘     └───────────────┘     └───────────────┘
```

---

## 🔄 Communication Flow

1. Client establishes a secure TLS connection
2. Server sends list of available songs
3. Client selects a song
4. Server sends metadata:

   * File size
   * MD5 hash
   * Total packets
5. Server streams data packets
6. Client buffers and detects missing packets
7. Client requests retransmission
8. Server retransmits missing packets
9. Client reconstructs file and verifies integrity

---

## 📦 Protocol Design

### 1. Song List

```
song1.mp3,song2.mp3,song3.mp3
```

### 2. Status Response

```
OK
```

or

```
ERROR
```

### 3. Metadata

```
<file_size>
<md5_hash>
<total_packets>
```

### 4. Packet Format

```
[4 bytes sequence number][4 bytes length][data]
```

### 5. End Marker

```
END_OF_T
```

### 6. Retransmission Request

```
MISSING:2,7,10
```

---

## 🔐 Security (SSL/TLS)

* Uses **TLS 1.2+ encryption**
* Server uses:

  * `server.crt` (certificate)
  * `server.key` (private key)
* Client verifies server certificate
* Prevents:

  * Eavesdropping
  * Data tampering
  * Man-in-the-middle attacks

---

## ⚙️ Features

* ✅ Multi-client support (threading)
* ✅ Secure communication (TLS)
* ✅ Packet-based streaming
* ✅ Simulated packet loss (10%)
* ✅ Retransmission mechanism
* ✅ File integrity check (MD5)
* ✅ Buffer-based playback

---

## 📊 Performance Evaluation (Sample)

| Metric           | Observation                            |
| ---------------- | -------------------------------------- |
| Transfer Time    | Depends on file size & network         |
| Packet Loss Rate | ~10% (simulated)                       |
| Retransmissions  | Successfully recovered missing packets |
| Throughput       | Stable under multiple clients          |

---

## 🚀 How to Run

### 1. Generate SSL Certificate

```
openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -days 365 -nodes
```

---

### 2. Start Server

```
python server.py
```

---

### 3. Run Client

```
python client.py
```

---

## 📁 Project Structure

```
project/
│── server.py
│── client.py
│── server.crt
│── server.key
│── songs/
│   ├── song1.mp3
│   ├── song2.mp3
```

---

## 🧠 Key Concepts Used

* Socket Programming (TCP)
* Multi-threading
* SSL/TLS Encryption
* Custom Protocol Design
* Error Detection & Recovery
* File Integrity Verification (MD5)

---

## 🏁 Conclusion

This project demonstrates a **secure, reliable, and scalable audio streaming system** using low-level socket programming. It successfully integrates **networking, security, and performance optimization techniques** into a real-world application.

---

## 👨‍💻 Author

karthik
koushik
harshit


---
