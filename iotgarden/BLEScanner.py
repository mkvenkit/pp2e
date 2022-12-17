"""

BLEScanner.py

This class uses BlueZ hciconfig, hcitool,  and hcidump tools to parse 
advertisement datafrom BLE peripherals. It then stores them in a database. 
This class also sends alerts via the IFTTT service.

Author: Mahesh Venkitachalam

"""

import sqlite3
import subprocess
from threading import Timer
import sys
import os
import time
import requests
from datetime import datetime

class BLEScanner:
    def __init__(self, dbname):
        """BLEScanner constructor"""
        self.T = 0
        self.H = 0
        # max values 
        self.TMAX = 30
        self.HMIN = 20
        # time stamp for last alert
        self.last_alert = time.time()
        # alert interval in seconds 
        self.ALERT_INT = 60
        # scan interval in seconds
        self.SCAN_INT = 10
        self._dbname = dbname
        self.hcitool = None
        self.hcidump = None
        self.task = None
        # -----------------------------------------------
        # peripheral allow list - add your devices here!
        # -----------------------------------------------
        self.allowlist = ["DE:74:03:D9:3D:8B"]
    
    def start(self):
        """Start BLE scan"""
        # start task 
        self.scan_task()
    
    def stop(self):
        """Stop BLE scan"""
        # stop timer
        self.task.cancel()

    def send_alert(self):
        """Send IFTTT alert if sensor data has exceeded the thresholds."""
        # check T, H 
        delta = time.time() - self.last_alert
        #print("delta: ", delta)
        if ((self.T > self.TMAX) or (self.H < self.HMIN)) and (delta > self.ALERT_INT):
            print("Triggering IFTTT alert!")
            key = '6zmfaOBei1DgdmlOgOi6C' # USE YOUR KEY HERE!
            url = 'https://maker.ifttt.com/trigger/TH_alert/json/with/key/' + key
            json_data = {"T": self.T, "H": self.H}
            r = requests.post(url, data = json_data)
            # save last alert
            self.last_alert = time.time()

    def start_scan(self):
        """starts the BlueZ tools required for scanning."""
        print("BLE scan started...")
        # reset device
        ret = subprocess.run(['sudo', '-n', 'hciconfig', 'hci0', 'reset'], stdout=subprocess.DEVNULL)
        print(ret)

        # start hcitool process
        self.hcitool = subprocess.Popen(['sudo', '-n', 'hcitool', 
            'lescan', '--duplicates'], stdout=subprocess.DEVNULL)
        
        # start hcidump process
        self.hcidump = subprocess.Popen(['sudo', '-n', 'hcidump', 
            '--raw'], stdout=subprocess.PIPE)
        
    def stop_scan(self):
        """stops BLE csan by killing BlueZ tools processes."""
        subprocess.run(['sudo', 'kill', str(self.hcidump.pid), '-s', 'SIGINT'])
        subprocess.run(['sudo', '-n', 'kill', str(self.hcitool.pid), '-s', "SIGINT"])       
        print("BLE scan stopped.")

    def parse_data(self, data):
        """Parses hcdump string and outputs MACID, name, manufacturer data"""
        
        # data format example
        # 04 3E 1C 02 01 02 01 8B 3D D9 03 74 DE 10 0F FF 22 08 0B 31 FE 49 4F 54 47 31 61 62 63 64 BD
        # ----------------------------------------------------------------I--O--T--G--1--a--b--c--d---

        fields = {}
        # parse MACID
        x = [int(val, 16) for val in data.split()]
        macid = ":".join([format(val, '02x').upper() for val in x[7:13][::-1]])
        # check if macid is in allowlist
        if macid in self.allowlist:
            # look at 6th byte to see PDU type
            if (x[5] == 0x02): # ADV_IND     
                print(data)
                fields["macid"] = macid
                # set pkt type
                #fields["ptype"] = "ADV_IND"       
                # parse data 
                fields["T"] = x[26]
                fields["H"] = x[27]
                name = "".join([format(val, '02x').upper() for val in x[21:26]])
                name = bytearray.fromhex(name).decode()
                fields["name"] = name
        return fields

    def parse_hcidump(self):
        """Parse output from hcidump"""
        data = ""
        (macid, name, T, H) = (None, None, None, None) 
        while True:
            line = self.hcidump.stdout.readline()
            line = line.decode()
            if line.startswith('> '):
                data = line[2:]
            elif line.startswith('< '):
                data = ""
            else:
                if data:
                    # concatenate lines
                    data += line
                    # a tricky way to remove white space
                    data = " ".join(data.split())
                    # parse data
                    fields = self.parse_data(data)
                    success = False
                    try:
                        macid = fields["macid"]
                        T = fields["T"]
                        H = fields["H"]
                        name = fields["name"]
                        success = True
                    except KeyError:
                        # skip this error, since this indicates
                        # invalid data 
                        pass
                    if success:
                        return (macid, name, T, H)

    def scan_task(self):
        """The scanning task which is run on a separate thread"""
        # start BLE scan 
        self.start_scan()
        # get data
        (macid, name, self.T, self.H) = self.parse_hcidump()
        # correct temperature offset
        self.T = self.T - 40
        print(self.T, self.H)
        # stop BLE scan 
        self.stop_scan()

        # send alert if required
        self.send_alert()

        # write to db
        # connect to database
        con = sqlite3.connect(self._dbname)
        cur = con.cursor()
        devID = macid
        # add data 
        with con:
            cur.execute("INSERT INTO iotgarden_data VALUES (?, ?, ?, ?, ?)", 
                (devID, name, datetime.now(), self.T, self.H))
        # commit changes
        con.commit()
        # close db
        con.close()

        # schedule the next task
        self.task = Timer(self.SCAN_INT, self.scan_task)
        self.task.start()   

# Use this for testing the class independently
def main():
    print("starting BLEScanner...")
    bs = BLEScanner("iotgarden.db")
    bs.start()
    data = None
    while True:
        try:
            (macid, name, T, H) = bs.parse_hcidump()
            #exit(0)
        except:
            bs.stop()
            print("stopped. Exiting")
            exit(0)
        
        print(macid, name, T, H)
        time.sleep(10)

if __name__ == '__main__':
    main()
