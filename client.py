import socket
import os
import sys
from idleRQ import *

PORT = 5104
ADDRESS = "127.0.0.1" #IP cil.informatics = 10.16.64.39
INFILENAME = "input.txt"
OUTFILENAME = "result_client.txt"
MAX_LINE_WIDTH = 500
MAX_FILE_SIZE = 10000
 
# def testClient():
#     print("testClient")
#     print("test import idle-rq")
#     testIdleRQ("client 8")
#     print("test trouble-maker with import idle-rq")
#     testTroubleMaker("client 5") 
# testClient()

# with open('./input.txt', 'r') as file:
#     file_contents = file.read()
# print(file_contents)

def main():
    content = ""
    # content = content[MAX_FILE_SIZE]
    # content[0] = 0

    # Create a pipe
    pipefd = os.pipe()
    
    # Fork a child process
    cpid = os.fork()
    
    if cpid == 0:  # Child process
        os.close(pipefd[1])  # Close the write-end of the pipe
        
        # Read from the pipe until EOF
        while True:
            buf = os.read(pipefd[0], 1)
            if not buf:
                break
            content += buf.decode()
        
        os.close(pipefd[0])  # Close the read-end of the pipe
        
    else:  # Parent process
        try:
            # Read file and append its content to 'content' variable
            with open(INFILENAME, "r") as file:
                for line in file:
                    content += line
            
            print(f"File read: {INFILENAME}")
        
            # Close the read-end of the pipe
            os.close(pipefd[0])
            
            # Send the content to the child process
            os.write(pipefd[1], content.encode())
            
            # Close the write-end of the pipe, sending EOF to the child process
            os.close(pipefd[1])
            
            # Wait for the child process to exit
            os.wait()
            sys.exit(0)
        except IOError:
            print(f"Error: Cannot open or close the file {INFILENAME}")
            sys.exit(1)

    # Create a socket
    try:
        socket_desc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        print(f"Error: Cannot create a socket: {e}")
        sys.exit(1)
    
    # Connect to the server
    servaddr = (ADDRESS, PORT)
    try:
        socket_desc.connect(servaddr)
        print(f"Connecting to {ADDRESS} on port {PORT} ...")
        print("Connection established.")
    except socket.error as e:
        print(f"Error: Cannot connect to the server: {e}")
        sys.exit(1)

    # Communicate with the server
    print(f"Sending Message:\n{content}")
    try:
        lenn = len(content)
        # sent_bytes = socket_desc.sendall(content.encode())
        sent_bytes = mysend(socket_desc, content, lenn, 0)
        if sent_bytes != lenn:
            print(f"Error: send() sent a different number of bytes than expected")
            sys.exit(1)
    except socket.error as e:
        print(f"Error: Cannot send using socket: {e}")
        sys.exit(1)

    # Receiving from the server
    # Uncomment this section if you expect a response from the server
    '''
    try:
        msgsize = socket_desc.recv(MAX_FILE_SIZE)
        if not msgsize:
            print("Error: Received empty message from the server")
            sys.exit(1)
        
        content = msgsize.decode()
        print(f"Message received, bytes: {lenn(content)}")
        print(f"The message is:\n{content}")
        
        # Invert case the entire buffer
        inverted_msg = invertcase(content)
        print(f"The message after case inversion:\n{inverted_msg}")
        
        # Writing the result to a file
        try:
            with open(OUTFILENAME, "w") as file:
                file.write(inverted_msg)
            print(f"File recently wrote: {OUTFILENAME}")
        except IOError:
            print("Error: Cannot write to a file")
            sys.exit(1)
    except socket.error as e:
        print(f"Error: Cannot receive using socket: {e}")
        sys.exit(1)
    '''

    # Close the socket
    close_status = socket_desc.close()
    if (close_status == -1):
        print("Error: Cannot close a socket")
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
