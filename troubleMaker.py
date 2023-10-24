import socket
import random

SEND_CHANCE = 80  # Chance to actually send (and not get lost)
CORRUPT_CHANCE = 20  # Chance to corrupt the frame given sending event
RAND_MAX = 100
# def testTroubleMaker(num):
#     print( "testTroubleMaker with parameter num: ", num)
    
# randomly toggle a bit of the frame
def corrupt(frame):
    bit = rand_lim(15)
    # print(bit)
    # print(frame)
    return frame ^ (1 << bit)

def mightsend(sockfile, framed, frame):
    print(frame)
    random_num = rand_lim(100)
    # print(f'rand: {random_num}')
    if random_num <= SEND_CHANCE:  # Chance to send and not get lost on the way
        random_num = rand_lim(100)
        if random_num <= CORRUPT_CHANCE:  # Chance to corrupt
            corrupted_frame = corrupt(frame)
            print(f"\t[[ CHANNEL: The frame {frame} is CORRUPTED into frame {corrupted_frame} ]]")
            frame = corrupted_frame
        try:
            print(f"send: {framed}")
            # print(f"send: {frame.to_bytes(2, byteorder='big')}")
            sockfile.send(bytes(framed.encode()))
        except socket.error:
            # The Secondary has closed the socket
            print("CHANNEL: [[ Sending failed, destination not available ]]")
    else:
        print(f"\t[[ CHANNEL: The frame {frame} is LOST ]]")
    
def printbytebits(byte):
    for i in range(8):
        on = testbit(byte, i)
        print(on, end='')
    print()

def tobytebits(bytei):
    bt = ''
    for i in range(8):
        # print(bytes(bytei.encode()))
        on = testbit(bytes(bytei.encode())[0], i)
        bt+=str(on)
    # print(int(bt.encode()))
    # print(bt)
    return bt
    # return int(bt.encode())
    
def printbits(frame):
    for i in range(16):
        on = testbit(frame, i)
        print(on, end='')
        if i == 7:
            print(" ", end='')
    print(f" ({frame}) ", end='')
    
def tobits(frame):
    b = ''
    for i in range(8):
        on = testbit(frame, i)
        b+=str(on)
    return b
    
def rand_lim(limit):
    """Return a random number uniformly between 0 and limit inclusive."""
    divisor = RAND_MAX/(limit+1)
    retval = random.random()*100 / divisor
    while retval > limit:
        retval = random.random()*100 / divisor
    return int(retval)

def testbit(frame, bitorder):
    return (frame >> bitorder) & 1

def setbit(frame, bitorder, value):
    mask = 1 << bitorder
    frame ^= (-value ^ frame) & mask
