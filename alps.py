#!/usr/bin/python

import serial
import binascii
import struct
import time
import datetime
from threading import *

class   Accel(Thread):
    def __init__(self, _port = ''):
        Thread.__init__(self)
        self.port_ = _port
        self.running_time_ = 1800
        self.time_table_ = []

    def isValid(self, data):
        data_array = bytearray(data)
        sum = 0 
        for byte in data_array[:len(data_array)-1]:
            sum += byte

        return  (sum % 256) == data_array[len(data_array) - 1]

    def setTimeTable(self, _time_table):
        _time_table.sort()
        self.time_table_ = _time_table
        print(self.time_table_)

    def run(self):
        if len(self.time_table_) != 0:
            while True:
                for item in self.time_table_:
                    now = datetime.datetime.now()
                    seconds = now.hour * 60 * 60 + now.minute * 60 + now.second
                    if seconds < (item * 60 * 60):
                        sleep_time = (item * 60 * 60) - seconds
                        print('Sleep : %d:%02d:%02d'%((sleep_time / 60 / 60), (sleep_time / 60) % 60, (sleep_time % 60)))
                        time.sleep(sleep_time)
                        self.readData(self.running_time_)
                now = datetime.datetime.now()
                seconds = now.hour * 60 * 60 + now.minute * 60 + now.second
                sleep_time = (24 * 60 * 60) - seconds
                print('Sleep : %d:%02d:%02d'%((sleep_time / 60 / 60), (sleep_time / 60) % 60, (sleep_time % 60)))
                time.sleep(sleep_time)


        else: 
            self.readData(0)
                


    def readData(self, running_time = 0):
        ser = serial.Serial( port=self.port_, baudrate=921600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        now = datetime.datetime.now()
        data_file = open('%d%02d%02d%02d%02d%02d.csv'%(now.year, now.month, now.day, now.hour, now.minute, now.second), 'at')
        previous_datetime = now 

        forever = False
        start_time = time.time()
        receive_buffer = b''

        while (running_time == 0) or (time.time() < (start_time + running_time)):
            receive_buffer = receive_buffer + ser.read(200)

            if (len(receive_buffer) >= 3) and (receive_buffer[0:3] != b'\xff\xc2\x81'):
                for i in range(len(receive_buffer) - 2):
                    if receive_buffer[i:i+3] == b'\xff\xc2\x81':
                        receive_buffer = receive_buffer[i:]

            if len(receive_buffer) >= 196:
                data = receive_buffer[:196]
                receive_buffer = receive_buffer[196:]

                now = datetime.datetime.now()
                timestamp = time.time()
                if self.isValid(data):
                    line = '%s'%timestamp
                    for i in range(3, 195, 6): 
                        x = struct.unpack('<h', data[i:i+2])[0]
                        y = struct.unpack('<h', data[i+2:i+4])[0]
                        z = struct.unpack('<h', data[i+4:i+6])[0]
                        line = line + ',%d,%d,%d'%(x,y,z)
                    print(line)
                    line = line + '\n'

                    if previous_datetime.hour != now.hour:
                        data_file.close()
                        data_file = open('%d%02d%02d%02d%02d%02d.csv'%(now.year, now.month, now.day, now.hour, now.minute, now.second), 'at')

                    data_file.write(line)

                elif len(data) != 0:
                    print('Invalid : %s'%(binascii.hexlify(data)))

                previous_datetime = now 

        data_file.close()
