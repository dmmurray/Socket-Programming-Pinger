# Dan Murray
# dmmurray@wpi.edu
# This file defined an ICMP pinger designed to mirror the ping function of most operating systems
# This file is based on the file ping.py at https://gist.github.com/pklaus/856268

import time
import socket
import struct
import select
import random
import asyncore
import signal
import sys
import numpy

# variable used for the ICMP echo request code
ICMP_ECHO_REQUEST = 8

ICMP_CODE = socket.getprotobyname('icmp')
ERROR_DESCR = {
    1: ' - Note that ICMP messages can only be '
       'sent from processes running as root.',
    10013: ' - Note that ICMP messages can only be sent by'
           ' users or processes with administrator rights.'
    }

__all__ = ['create_packet', 'do_one', 'ping', 'PingQuery']


# global variables to be used when SIGINT is received
globhostAddr = ''
globptrans = 0
globprecv = 0
globrttimes = []

# The summarize() function returns a string with the ping summary
def summarize():
    ptrans = globptrans
    precv = globprecv
    rttimes = globrttimes
    returnstring = '\n--- ' + globhostAddr + ' ping statistics ---\n' + str(ptrans) + ' packets transmitted, ' + str(precv) + ' packets received, '
    ploss = round((1 - (float(precv) / ptrans)) * 100.0, 4)
    returnstring += str(ploss) + '%' + ' packet loss\n'
    rttarray = numpy.array(rttimes)
    rttmin = min(rttimes)
    rttmin = round(rttmin * 1000.0, 5)
    returnstring += 'round-trip min/avg/max/stddev = ' + str(rttmin)
    rttmean = numpy.mean(rttarray)
    rttmean = round(rttmean * 1000.0, 5)
    returnstring += '/' + str(rttmean)
    rttmax = max(rttimes)
    rttmax = round(rttmax * 1000.0, 5)
    returnstring += '/' + str(rttmax)
    rttstdev = numpy.std(rttarray)
    rttstdev = round(rttstdev * 1000.0, 5)
    returnstring += '/' + str(rttstdev) + ' ms'
    return returnstring

# The signal_handler() is invoked when the SIGINT signal is received
def signal_handler(signal, frame):
    printstring = summarize()
    print(printstring)
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# checksum creates the checksum for a particular packet given the source_string
def checksum(source_string):
    sum = 0
    count_to = (len(source_string) / 2) * 2
    count = 0
    while count < count_to:
        this_val = ord(source_string[count + 1])*256+ord(source_string[count])
        sum = sum + this_val
        sum = sum & 0xffffffff
        count = count + 2
    if count_to < len(source_string):
        sum = sum + ord(source_string[len(source_string) - 1])
        sum = sum & 0xffffffff
    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    # Swap bytes
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


# create_packet() creates the packet to be sent
def create_packet(id, seqnum):
    """Create a new echo request packet based on the given "id"."""
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, 0, id, seqnum)
    data = 192 * 'Q'
    # Calculate the checksum on the data and the dummy header.
    my_checksum = checksum(header + data)
    # Now that we have the right checksum, we put that in. It's just easier
    # to make up a new header than to stuff it into the dummy.
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0,
                         socket.htons(my_checksum), id, seqnum)
    return header + data


# do_one() sends one ping to the given dest_addr. timeout is used to define how long a packet
#     will wait for a response. do_one() returns either the delay for the successfully received
#     packet, or returns no delay and an invalid address in the event of a timeout.
def do_one(dest_addr, timeout=1, seqnum=1):
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, ICMP_CODE)
    except socket.error as e:
        if e.errno in ERROR_DESCR:
            # Operation not permitted
            raise socket.error(''.join((e.args[1], ERROR_DESCR[e.errno])))
        raise # raise the original error
    try:
        host = socket.gethostbyname(dest_addr)
    except socket.gaierror:
        return
    # Maximum for an unsigned short int c object counts to 65535 so
    # we have to sure that our packet id is not greater than that.
    packet_id = int((id(timeout) * random.random()) % 65535)
    packet = create_packet(packet_id, seqnum)
    while packet:
        # The icmp protocol does not use a port, but the function
        # below expects it, so we just give it a dummy port.
        sent = my_socket.sendto(packet, (dest_addr, 1))
        packet = packet[sent:]
    global globptrans
    globptrans += 1
    delay = receive_ping(my_socket, packet_id, time.time(), timeout)
    if delay:
        global globprecv
        global globrttimes
        globprecv += 1
        globrttimes.append(delay)
    my_socket.close()
    return delay

# receive_pint() receives the ping from the socket and prints information about the received packet
def receive_ping(my_socket, packet_id, time_sent, timeout):
    time_left = timeout
    while True:
        started_select = time.time()
        ready = select.select([my_socket], [], [], time_left)
        how_long_in_select = time.time() - started_select
        if ready[0] == []: # Timeout
            return
        time_received = time.time()
        rec_packet, addr = my_socket.recvfrom(1024)
        icmp_header = rec_packet[20:28]
        type, code, checksum, p_id, sequence = struct.unpack(
            'bbHHh', icmp_header)
        bytes = len(rec_packet)
        address = addr[0]
        ttl = struct.unpack('B', rec_packet[8])[0]
        roundtriptime = time_received - time_sent
        roundtriptime = round(roundtriptime * 1000.0, 4)
        print(str(bytes) + " bytes from " + str(address) + ": icmp_seq=" + str(sequence) + " ttl=" + str(ttl) + " time=" + str(roundtriptime) + " ms")
        if p_id == packet_id:
            return time_received - time_sent
        time_left -= time_received - time_sent
        if time_left <= 0:
            return


# ping() sends count pings to dest_addr, and when the program is terminated either by finishing successfully
#     or by receiving the SIGINT signal, prints a summary of the program execution.
def ping(dest_addr, count):
    global globhostAddr
    globhostAddr = dest_addr
    timeout = 1
    i = 0
    print('PING ' + str(dest_addr) + '...')
    if count:
        while i < count:
            seqnum = i + 1
            delay = do_one(dest_addr, timeout, seqnum)
            if delay == None:
                print('Request timed out')
            i += 1
            if i == count:
                print(summarize())
    else:
        while 1:
            i += 1
            delay = do_one(dest_addr, timeout, i)
            if delay == None:
                print('Request timed out')
    print('')


# The following is the command line that the user interacts with
if __name__ == '__main__':
    arguments = raw_input('>')
    if ' ' in arguments:
        hostAddr, numRequests = arguments.split(' ', 2)
        ping(hostAddr, int(numRequests))
    else:
        hostAddr = arguments
        ping(hostAddr, 0)