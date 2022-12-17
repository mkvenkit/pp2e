// ****************************************************************************
// server.js
// 
// This JavaScript code fetches the sensor data asychronously 
// from the Bottle web server and generates the HTML elements 
// required to display it. 
// 
// Author: Mahesh Venkitachalam
//
// ****************************************************************************

// async function that fetches data from server 
async function fetch_data() { 
    let response = await fetch('thdata');
    devices_json = await response.json();
    console.log('updating HTML...');
    devices = devices_json["devices"];
    let strHTML = "";
    var ts = new Date().getTime();
    for (let i = 0; i < devices.length; i++) {
        // console.log(devices[i].macid) 
        strHTML = '<div class="thdata">';
        strHTML += '<span>' + devices[i].name + '(' + devices[i].macid 
            + '): </span>';
        strHTML += '<span>T = ' + devices[i].T + ' C (' + (9.0*devices[i].T/5.0 + 32.0) + ' F),</span>'; 
        strHTML += '<span> H = ' + devices[i].H + ' % </span>'; 
        strHTML += '</div>'; // thdata
        // create image div 
        strHTML += '<div class="imdiv"><img src="image/' + 
            devices[i]["macid"] + '?ts=' + ts + '"></div>';
        // add divider 
        strHTML += '<hr/>';
    }

    // set HTML data 
    document.getElementById("sensors").innerHTML = strHTML;
};

// fetch once on load 
window.onload = function() {
    fetch_data();
};

// Now fetch data every 30 seconds  
setInterval(fetch_data, 30000);

