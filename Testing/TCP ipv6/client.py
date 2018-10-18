import socket

hostIP = "fe80::2117:1a0a:4ec3:b970%26"  # localhost
hostPort = 5005
message = "Hello, World!"

sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
sock.connect((hostIP, hostPort, 0, 0))
sock.sendall(message.encode())