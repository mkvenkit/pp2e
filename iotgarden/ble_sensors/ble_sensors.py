"""

ble_sensors.py 

CircuitPython code for Adafruit BLE Sense boards. This program reads 
data from the built-in Temperature and Humidity sensors, and puts the 
data in the BLE advertisement packet.

Author: Mahesh Venkitachalam

"""

import time
import struct
import board
import adafruit_bmp280
import adafruit_sht31d
from adafruit_ble import BLERadio
from adafruit_ble.advertising import Advertisement, LazyObjectField
from adafruit_ble.advertising.standard import ManufacturerData, ManufacturerDataField

# Derived from adafruit_ble class Advertisement
class IOTGAdvertisement(Advertisement):
    flags = None
    match_prefixes = (
        struct.pack(
             "<BHBH", # prefix format 
            0xFF,     # 0xFF is "Manufacturer Specific Data" as per BLE spec
            0x0822,   # 2 byte company ID
            struct.calcsize("<H9s"), # data format 
            0xabcd # our ID
        ), # comma required - a tuple is expected 
    )
    manufacturer_data = LazyObjectField(
        ManufacturerData,
        "manufacturer_data",
        advertising_data_type=0xFF, # 0xFF is "Manufacturer Specific Data" as per BLE spec
        company_id=0x0822,          # 2 byte company ID
        key_encoding="<H",
    )
    # set manufacturer data field 
    md_field = ManufacturerDataField(0xabcd, "<9s")


def main():

    # initialize I2C
    i2c = board.I2C()

    # initialize sensors 
    bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
    sht31d = adafruit_sht31d.SHT31D(i2c)

    # initialize  BLE
    ble = BLERadio()

    # create custom advertisement object 
    advertisement = IOTGAdvertisement()
    # set device name 
    ble.name = "IOTG1" 
    # set initial value 
    # will use only first 5 chars of name 
    advertisement.md_field = ble.name[:5] + "0000"
    # BLRE advertising interval in seconds
    BLE_ADV_INT = 0.2
    # start BLE advertising 
    ble.start_advertising(advertisement, interval=BLE_ADV_INT)

    # main loop 
    while True:
        # print values - this will be available on serial 
        print("Temperature: {:.1f} C".format(bmp280.temperature))
        print("Humidity: {:.1f} %".format(sht31d.relative_humidity))
        # get sensor data         
        T = int(bmp280.temperature)
        H = int(sht31d.relative_humidity)
        # stop advertsing 
        ble.stop_advertising()
        # update advertisement data 
        advertisement.md_field = ble.name[:5] + chr(T) + chr(H) + "00"
        # start advertising 
        ble.start_advertising(advertisement, interval=BLE_ADV_INT)
        # sleep for 2 seconds 
        time.sleep(2)

# call main 
if __name__ == "__main__":
    main()
