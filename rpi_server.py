import socket

s = socket.socket()
host = '192.168.0.105'  # ip of raspberry pi
port = 12345
s.bind((host, port))

s.listen(5)
while True:
    c, addr = s.accept()
    print('Got connection from', addr)
    c.send(b'fuck off you goddamn piece of shit!')
    c.close()
