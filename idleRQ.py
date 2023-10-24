from troubleMaker import *

PARITY_BIT = 15
SEQ_BIT = 14
LAST_INDICATOR_BIT = 13
ACK_BIT = 12
TIMEOUT_MSEC = 1200 #milli secs
BUFSIZE = 10000
 
# def testIdleRQ(num):
#     print( "testIdleRQ with parameter num: ", num)
#     print("test import trouble-maker")
#     testTroubleMaker(num)
    
def mysend(sockfile, buf, len, flags):
    # Convert bytes to bytearray for mutable operations
    tmp = bytearray(buf.encode())

    # Print the content of the buffer as byte bits
    print("Buf ({}):".format(len))
    for byte in tmp:
        printbytebits(byte)

    # Make frames
    # frames = makeframes(tmp, len)
    frames = makeframes(buf, len)
    n = len
    print("Frames ({}):".format(n))

    for i in range(n):
        print("> Sending I-frame {}: ".format(i), end='')
        printbits(frames[i])
        printstat(frames[i])
        mightsend(sockfile, tobits(frames[i]), frames[i])

        # Set a timeout for recv()
        sockfile.settimeout(TIMEOUT_MSEC / 1000.0)

        try:
            print("Timer Started: Waiting for an ACK frame ...")
            ack = -1
            ack_data = sockfile.recv(BUFSIZE, ack)
            status = int.from_bytes(ack_data, byteorder='big')
            print(f"recv: {ack_data}")
            print(status)
            
            if status == 0:
                # the Secondary has closed the socket
                print("Secondary has closed connection, indicating proper transmission. ACK frame not needed. Primary process is terminating.")
                break
            elif (status < 2): # Timer expired
                print("TIMEOUT: No response within %d millisecs. Retransmit this I-frame again.\n", TIMEOUT_MSEC)
                i-=1
                continue

            isack = testbit(ack, ACK_BIT)
            corrup = corrupted(ack)
            print(f">  Receiving {'a corrupted' if corrup else 'ACK' if isack else 'NAK'} frame: ", end='')
            printbits(ack)
            printstat(ack)

            if isack:
                NS = testbit(frames[i], SEQ_BIT)
                NR = testbit(ack, SEQ_BIT)
                P0 = NS == NR
                P1 = not corrup

                if P0:
                    if P1:
                        print("Timer Stopped: Valid ACK N(S)=N(R)={} is received.".format(NR))
                    else:
                        print("ACK frame received is corrupted")
                        print("Resend this I-frame again.")
                        i -= 1
                else:
                    print("Error: Expected N(S)=N(R)={}, got N(S)={}".format(NR, NS))

                    if not P1:
                        print("Error: Wrong Seq ACK and corrupted")
                    else:
                        print("Error: Wrong Seq ACK and not corrupted")
            else:
                print("Resend this I-frame again.")
                i -= 1
                continue

        except socket.timeout:
            print("TIMEOUT: No response within {} millisecs. Retransmit this I-frame again.".format(TIMEOUT_MSEC))
            i -= 1
        except Exception as e:
            print("Error:", e)

    print("All {} frames sent".format(n))
    return len

def myrecv(sockfile, buf, len, flags):
    # frames = [0] * (len + 1)
    frames = bytearray(len + 1)
    i = 0  # Frame number that we are waiting for

    while True:
        # PresentState=WTIFM; Waiting for event: IRCVD
        print("Waiting for an I-frame ...")
        frame_data = sockfile.recv(2)
        
        if not frame_data:
            print("Primary has closed connection, unexpected behavior!")
            return i
        
        frame = int.from_bytes(frame_data, byteorder='big')
        corrup = corrupted(frame)
        NS = testbit(frame, SEQ_BIT)
        Vr = i % 2
        P0 = NS == Vr
        P1 = not corrup
        P2 = NS == (not Vr)
        last = testbit(frame, LAST_INDICATOR_BIT) and P0 and P1
        print(f" < Receiving {'a corrupted ' if corrup else 'the last ' if last else ''}I-frame {i}: ", end='')
        printbits(frame)
        printstat(frame)
        ack = 0
        X = NS
        # isack = 0
        
        if not P1:
            # TxNAK(X);
            isack = 0
        else:
            if P2:
                isack = 1
                print("The I-frame order is invalid. Duplication detected.")
                print(f"Expected N(S)=Vr={Vr}, got N(S)={X}")
            elif P0:
                frames[i] = frame
                isack = 1
                i += 1
            else:
                print("P1 and not P2 and not P0, impossible")

        ack = setbit(ack, ACK_BIT, isack)
        ack = setbit(ack, SEQ_BIT, X)
        ack = setbit(ack, PARITY_BIT, parity(ack))
        print(f">  Sending {'ACK' if testbit(ack, ACK_BIT) else 'NAK'} frame: ", end='')
        printbits(ack)
        printstat(ack)
        mightsend(sockfile, ack)

        # Check for the last frame
        if last:
            print("Got the last frame, stopped")
            break

    # Join packets from frames together into buf
    print("Joining frames ...")
    joinframes(frames, buf, i)
    return len(buf)


def joinframes(frames, buf, len):
    for i in range(len):
        buf[i] = 0
        for j in range(8):
            if testbit(frames[i], j):
                buf[i] |= 1 << j
    buf[len] = 0

def makeframes(buf, len):
    print(buf)
    frames = bytearray(len + 1)
    # frames = [0] * (len + 1)
    fNo = 0 # current frame number that we are filling bits into
    done = False
    while not done:
        frames[fNo] = 0
        for i in range(8):
            if int(tobytebits(buf[fNo])) & (1 << i):
                frames[fNo] |= 1 << i
        
        # add seqNo bit
        if fNo % 2:
            # frames[fNo] |= 1 << SEQ_BIT
            setbit(frames[fNo], SEQ_BIT, 1)
        # print(fNo)
        if tobytebits(buf[fNo + 1]) == 0 or fNo + 1 >= len - 1:
            # frames[fNo] |= 1 << LAST_INDICATOR_BIT
            setbit(frames[fNo], LAST_INDICATOR_BIT, 1)
            done = True
            frames[fNo + 1] = 0
        
        # add parity bit
        if parity(frames[fNo]):
            # frames[fNo] |= 1 << PARITY_BIT
            setbit(frames[fNo], PARITY_BIT, 1)
            
        fNo += 1
    
    return frames

def parity(frame):
    result = 0
    for i in range(PARITY_BIT):
        result ^= (frame >> i) & 1
    return result

def corrupted(frame):
    return parity(frame) != ((frame >> PARITY_BIT) & 1)

def printstat(frame):
    print("\n")