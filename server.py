import socket
import os
import sys
from idleRQ import *
 
PORT = 5104
BUFSIZE = 10000
OUTFILENAME = "result_server.txt"

# def testServer():
#     print("testServer")
#     print("test import idle-rq")
#     testIdleRQ("server 8")
#     print("test trouble-maker with import idle-rq")
#     testTroubleMaker("server 5")
# testServer()

# invert case of every characters inside the string
def invertcase(s):
    print(s)
    result = []
    for char in s:
        if char.isalpha():
            result.append(chr(ord(char) ^ (1 << 5)))
        else:
            result.append(char)
    return ''.join(result)

def main():
    bufsize = BUFSIZE
    msgbuffer = bytearray(bufsize)
    parent_pid = os.getpid()
    
    # Create a pipe
    pipefd = os.pipe()
    
    # Fork a child process
    cpid = os.fork()
    
    if cpid == 0:  # Child process
        os.close(pipefd[0])  # Close the read-end of the pipe
    else:  # Parent process
        os.close(pipefd[1])  # Close the write-end of the pipe
        
        msgsize = os.read(pipefd[0], bufsize)  # Read from the pipe
        os.close(pipefd[0])  # Close the read-end of the pipe
        
        print(f"Message received, bytes: {len(msgsize)}")
        msgbuffer = msgsize.decode()
        print(f"The message is:\n{msgbuffer}")
        
        # Invert case the entire buffer
        inverted_msg = invertcase(msgbuffer)
        print(f"The message after case inversion:\n{inverted_msg}")
        
        # Writing the result to a file
        try:
            with open(OUTFILENAME, "w") as file:
                file.write(inverted_msg)
            print(f"File recently wrote: {OUTFILENAME}")
        except IOError:
            print("Error: Cannot write to a file")
            sys.exit(1)
        
        # Wait for the child process to exit before exiting
    # os.wait()
        # sys.exit(0)

    # Server part
    # Create a socket
    try:
        socket_desc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        print(f"Error: Cannot create a socket: {e}")
        sys.exit(1)
        
        # Try reusing the socket with the same port when it says that the address
        # is already in use when binding
    socket_desc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind the socket
    addrport = ('', PORT)
    try:
        socket_desc.bind(addrport)
    except socket.error as e:
        print(f"Error: Cannot bind a socket: {e}")
        sys.exit(1)
        
    # Listen for connections on the socket
    qLimit = 10
    try:
        socket_desc.listen(qLimit)
    except socket.error as e:
        print(f"Error: Cannot listen for a socket: {e}")
        sys.exit(1)

    print(f"Accepting a connection on port {PORT} ...")
    # Accept a connection on the socket
    client_socket, clientAddr = socket_desc.accept()
        
    print(f"A client from port {clientAddr[1]} is connected.")
        
    # Communicate with the client
    try:
        msgsize = myrecv(client_socket, msgbuffer, bufsize, 0)
        if not msgsize:
            client_socket.close()
            sys.exit(1)
            
        # msgbuffer = msgsize
        msgbuffer = msgsize.decode()
        print(f"Message received, bytes: {len(msgbuffer)}")
        print(f"The message is:\n{msgbuffer}")
            
        # Invert case the entire buffer
        inverted_msg = invertcase(msgbuffer)
        print(f"The message after case inversion:\n{inverted_msg}")
            
            # Send the inverted message back to the client
        client_socket.sendall(inverted_msg.encode())
        client_socket.close()
    except socket.error as e:
        print(f"Error: Cannot receive/send using socket: {e}")
        client_socket.close()
        sys.exit(1)
        
        # Close the socket and free the port
    socket_desc.close()
    sys.exit(0)

if __name__ == "__main__":
    main()
