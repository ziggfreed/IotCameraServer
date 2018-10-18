import socket
  
UDP_IP = "fe80::2117:1a0a:4ec3:b970%26" # = 0.0.0.0 u IPv4
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
sock.settimeout(10.0)
sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print("received message:", data)