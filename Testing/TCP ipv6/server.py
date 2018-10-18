import socket
import time
  
hostIP = "fe80::2117:1a0a:4ec3:b970%26" # = 0.0.0.0 u IPv4
hostPort = 5005

sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
sock.settimeout(10.0)
sock.bind((hostIP, hostPort))
sock.listen(1)

conn, addr = sock.accept()
time.sleep(1)
print ('Server: Connected by', addr)
if True: # answer a single request
    data = conn.recv(1024)
    print(data)
    conn.close()