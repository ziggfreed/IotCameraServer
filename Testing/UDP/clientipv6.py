import socket

UDP_IP = "fe80::2117:1a0a:4ec3:b970%26"  # localhost
UDP_PORT = 5005
MESSAGE = "Hello, World!"

sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
# sock.connect((UDP_IP, UDP_PORT, 0, 0))
sock.sendto(MESSAGE.encode(), (UDP_IP, UDP_PORT))