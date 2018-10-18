# IotCameraServer

This project is to set up a simple smart camera system with IOT security features for an assignment for uni. It uses two raspberry pi devices, one to capture images and send them to the other device which detects motion and faces. 


Note about IPv6:
I had a lot of trouble getting IPv6 working since there is different implementations between windows and raspbian. In Raspbian you will need to get the IPv6 Link-local address using "ip -6 add". Take note of the number at the start, this will need to be used in the command "serverSocket.connect((self.addr[0], 5996, 0, >>0<<))" since it specifies the interface. On windows it uses the %xx at the end of the address eg: fe80::9390%12
