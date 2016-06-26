import sys
import struct
sys.path.append("../crazyflie-clients-python/src/cflib")

from cflib.drivers import crazyradio
from cflib.crtp.crtpstack import CRTPPacket
from cflib.crtp.crtpstack import CRTPPort
from cflib.crazyflie import log

def GetVBat():
    cr = crazyradio.Crazyradio()
    cr.set_channel(0)
    cr.set_data_rate(cr.DR_2MPS)

    pk = CRTPPacket()

    # Create the log block
    pk.set_header(CRTPPort.LOGGING, log.CHAN_SETTINGS)
    pk.data = ([log.CMD_CREATE_BLOCK, 0x01, 0x07, 42])
    packet = bytearray([pk.header]) + pk.data

    retry = True
    while retry:
        res = cr.send_packet(packet)
        if res.ack:
            if len(res.data) >= 2:
                if res.data[0] | 0x3 << 2 == pk.header:
                    if res.data[1] == log.CMD_CREATE_BLOCK:
                        retry = False
    print("Log created with return value 0x{:02x}".format(res.data[2]))

    # Start the log block
    pk.set_header(CRTPPort.LOGGING, log.CHAN_SETTINGS)
    pk.data = ([log.CMD_START_LOGGING, 0x01, 50])
    packet = bytearray([pk.header]) + pk.data
    retry = True
    while retry:
        res = cr.send_packet(packet)
        if res.ack:
            if len(res.data) >= 2:
                if res.data[0] | 0x3 << 2 == pk.header:
                    if res.data[1] == log.CMD_START_LOGGING:
                        retry = False
    print("Log started with return value 0x{:02x}".format(res.data[2]))

    # Now loop forever sending empty CRTP packets, waiting for log data in the ACK.
    pk.set_header(CRTPPort.COMMANDER, 0)
    roll = 0.0
    pitch = 0.0
    yaw = 0.0
    thrust = 0
    pk.data = bytearray(struct.pack("f", roll))
    pk.data += bytearray(struct.pack("f", pitch))
    pk.data += bytearray(struct.pack("f", yaw))
    pk.data += bytearray(struct.pack("H", thrust))
    packet = bytearray([pk.header]) + pk.data

    logPacket = CRTPPacket()
    logPacket.set_header(CRTPPort.LOGGING, log.CHAN_LOGDATA)

    while True:
        res = cr.send_packet(packet)
        if res.ack:
            if len(res.data) >= 2:
                if res.data[0] | 0x3 << 2 == logPacket.header:
                    if res.data[1] == 0x01:
                        print(struct.unpack("<f", res.data[5:])[0])


def DownloadTOC():
    cr = crazyradio.Crazyradio()
    cr.set_channel(0)
    cr.set_data_rate(cr.DR_2MPS)

    pk = CRTPPacket()
    pk.set_header(CRTPPort.LOGGING, log.CHAN_TOC)

    pk.data = ([log.CMD_TOC_INFO])
    packet = bytearray([pk.header]) + pk.data

    retry = True

    while retry:
        print("Sending TOC info request...")
        res = cr.send_packet(packet)
        if res.ack:
            print("ACK received")
            if len(res.data) >= 2:
                if res.data[0] | 0x3 << 2 == pk.header:
                    if res.data[1] == log.CMD_TOC_INFO:
                        retry = False

    print("Received TOC info!")
    print("Entire ACK: " + "".join("0x%02x " % b for b in res.data))
    tocSize = res.data[2]
    #tocChkSum = res.data[3:6]
    tocMaxPacket = res.data[7]
    tocMaxOps = res.data[8]
    print("TOC size={:d}".format(tocSize))
    #print("TOC chksum={:d}".format(tocChkSum))
    print("TOC MaxPacket={:d}".format(tocMaxPacket))
    print("TOC MaxOps={:d}".format(tocMaxOps))

    for i in range(0, tocSize):
        pk.data = ([log.CMD_TOC_ELEMENT, i])
        packet = bytearray([pk.header]) + pk.data

        retry = True
        while retry:
            #print("Sending TOC Element request for {:d}".format(i))
            res = cr.send_packet(packet)
            if res.ack:
                if len(res.data) >= 2:
                    if res.data[0] | 0x3 << 2 == pk.header:
                        if res.data[1] == log.CMD_TOC_ELEMENT:
                            if res.data[2] == i:
                                retry = False

        strs = bytes.decode(bytes(res.data[4:])).split("\0")

        print("Element {:d} of type {:d} is called \"{:s}\" of group \"{:s}\"".format(res.data[2], res.data[3], strs[1], strs[0]))


        #print(bytes.decode(bytes(res.data[4:])).split("\0")[0])


def ArrayTest():
    array = bytearray([0x01, 0x02, 0x03])
    print("Val0: 0x{:02x}".format(array[0]))
    print("Val1: 0x{:02x}".format(array[1]))
    print("Val2: 0x{:02x}".format(array[2]))

def GarbageBytesTest():
    cr = crazyradio.Crazyradio()
    cr.set_channel(0)
    cr.set_data_rate(cr.DR_2MPS)

    pk = CRTPPacket()
    pk.set_header(CRTPPort.COMMANDER, 0)

    roll = 0.0
    pitch = 0.0
    yaw = 0.0
    thrust = 0
    pk.data = bytearray(struct.pack("f", roll))
    pk.data += bytearray(struct.pack("f", pitch))
    pk.data += bytearray(struct.pack("f", yaw))
    pk.data += bytearray(struct.pack("H", thrust))
    packet = bytearray([pk.header]) + pk.data

    garbageBytes = 0
    totalSends = 0

    run = True
    while run:
        res = cr.send_packet(packet)
        totalSends += 1
        if res.ack:
            if res.data[0] == 0xF3:
                print("".join("0x%02x " %b for b in res.data))
                run = False
            elif res.data[0] == 0xF7:
                print("".join("0x%02x " % b for b in res.data))
                run = False
            else:
                for byte in res.data:
                    garbageBytes += 1
    # print("Received " + garbageBytes + " garbage bytes in " + totalSends + " packets")
    print(garbageBytes)
    print(totalSends)

#Start of tests!
#GarbageBytesTest()
#DownloadTOC()
GetVBat()
#ArrayTest()
