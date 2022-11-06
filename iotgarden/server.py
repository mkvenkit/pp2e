"""

server.py

This program creates a Bottle.py based web server. It also creates a 
plot from the sensor data. 

Author: Mahesh Venkitachalam

"""
from bottle import Bottle, route, template, response, static_file
from matplotlib import pyplot as plt
import io
import sqlite3

class IOTGServer:

    def __init__(self, dbname, host, port):
        """constructor for IGServer"""
        self._dbname = dbname
        self._host = host
        self._port = port
        # create bottle object 
        self._app = Bottle()
    
    def get_data(self, macid):
        # connect to database
        con = sqlite3.connect(self._dbname)
        cur = con.cursor()
        data = []
        for row in cur.execute("SELECT * FROM iotgarden_data where DEVID = :dev_id LIMIT 100", {"dev_id" : macid}):
            data.append((row[3], row[4]))
        # commit changes
        con.commit()
        # close db
        con.close()
        
        return data

    def plot_image(self, macid):
        """Create a plot of sensor data by reading database"""
        # get data 
        data = self.get_data(macid)
        # create plot 
        plt.legend(['T', 'H'], loc='upper left')
        plt.plot(data)
        # save to a buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        # reset stream position to start
        buf.seek(0) 
        # read image data as bytes 
        img_data = buf.read()
        # set response type
        response.content_type = 'image/png'
        # return image data as bytes 
        return img_data

    def main_page(self):
        """main HTML page"""
        response.content_type = 'text/html'
        strHTML = """
<!DOCTYPE html>
<html>
<head>
<link href="static/style.css" rel="stylesheet">
<script src="static/server.js"></script>
</head>
<body>
<div id = "title">The IoT Garden </div>
<hr/>
<div id="sensors"></div>
</body>
</html>"""
        return strHTML

    def thdata(self):
        """Connect to database and retrieve latest sensor data""" 
        # connect to database
        con = sqlite3.connect(self._dbname)
        cur = con.cursor()
        # set up a device list 
        devices = []
        # get unique device list from db
        devid_list = cur.execute("SELECT DISTINCT DEVID FROM iotgarden_data")
        #print(devid_list)
        for devid in devid_list:
            for row in cur.execute("SELECT * FROM iotgarden_data where DEVID = :devid ORDER BY TS DESC LIMIT 1", 
                {"devid" : devid[0]}):
                devices.append({'macid': row[0], 'name': row[1], 'T' : row[3], 'H': row[4]})
            
         # commit changes
        con.commit()
        # close db
        con.close()
        # return device dictionary
        return {"devices" : devices}

    def st_file(self, filename):
        """serves static files"""
        return static_file(filename, root='./static')

    def run(self):
        # ----------
        # add routes:
        # ----------
        # T/H data
        self._app.route('/thdata')(self.thdata)
        # plot image
        self._app.route('/image/<macid>')(self.plot_image)
        # static files - CSS, JavaScript
        self._app.route('/static/<filename>')(self.st_file)   
        # main HTML page
        self._app.route('/')(self.main_page)
        
        # start server
        self._app.run(host=self._host, port=self._port)
