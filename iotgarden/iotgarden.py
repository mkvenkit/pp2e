"""

iotgarden.py 


Main program for the IoT Garden project. Sets up database, starts the Bottle 
web server, and the BLE scanner.

Author: Mahesh Venkitachalam

"""

import argparse
import sqlite3 
from BLEScanner import BLEScanner
from server import IOTGServer

def print_db(dbname):
    """Prints contents of database."""
    # connect to database
    con = sqlite3.connect(dbname)
    cur = con.cursor()
    for row in cur.execute("SELECT * FROM iotgarden_data"):
       print (row)

def setup_db(dbname):
    """Set up the database."""
    # connect to database - will create new if needed 
    con = sqlite3.connect(dbname)
    cur = con.cursor()
    # drop if table exists
    cur.execute("DROP TABLE IF EXISTS iotgarden_data") 
    # Create table
    cur.execute("CREATE TABLE iotgarden_data(DEVID TEXT, NAME TEXT, TS DATETIME, T NUMERIC, H NUMERIC)")

def main():
    print("starting iotgarden...")

    # set up cmd line argument parser
    parser = argparse.ArgumentParser(description="iotgarden.")
    # add arguments
    parser.add_argument('--createdb', action='store_true', required=False)
    parser.add_argument('--lsdb', action='store_true', required=False)
    parser.add_argument('--hostname', dest='hostname', required=False)
    args = parser.parse_args()

    # set database name
    dbname = 'iotgarden.db'

    if (args.createdb):
        print("Setting up database...")
        setup_db(dbname)
        print("done. exiting.")
        exit(0)

    if (args.lsdb):
        print("Listing database contents...")
        print_db(dbname)
        print("done. exiting.")
        exit(0)

    # set hostname
    hostname = 'iotgarden.local'
    if (args.hostname):
        hostname = args.hostname

    # create BLE scanner 
    bs = BLEScanner(dbname)
    # start BLE 
    bs.start()

    # create server
    server = IOTGServer(dbname, hostname, 8080)
    # run server
    server.run()

# call main 
if __name__ == "__main__":
    main()
