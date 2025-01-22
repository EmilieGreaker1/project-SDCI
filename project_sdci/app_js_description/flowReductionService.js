/**
 *  Author: Emilie GREAKER greaker@insa-toulouse.fr
 *  Author: Y-Quynh Nguyen yqnguyen@insa-toulouse.fr
 *  File : saturationService.js
 *  Version : 0.1.0
 */

var express = require('express')
var app = express()
app.use(express.json()) // for parsing application/json
var request = require('request');
var argv = require('yargs').argv;

var LOCAL_ENDPOINT = {IP : argv.local_ip, PORT : argv.local_port, NAME : argv.local_name};
var REMOTE_ENDPOINT = {IP : argv.remote_ip, PORT : argv.remote_port, NAME : argv.remote_name};

const E_OK              = 200;
const E_CREATED         = 201;
const E_NOT_FOUND       = 404;
const E_ALREADY_EXIST   = 500;

// Database of the gateways
var db = {
        gateways : new Map()
    };

// Add new gateway to database
function addNewGateway(gw) {
    var res = -1;
    if (!db.gateways.get(gw.Name)) {
        db.gateways.set(gw.Name, gw);
        res = 0;
    }
    return res;
}

// Remove gateway from database
function removeGateway(gw) {
    if (db.gateways.get(gw.Name))
        db.gateways.delete(gw.Name);
}
    
// Function to POST
function doPOST(uri, body, onResponse) {
    request({method: 'POST', uri: uri, json : body}, onResponse); 
}

app.post('/gateways/register', function(req, res) {
    console.log(req.body);
    var result = addNewGateway(req.body);
    if (result === 0)
        res.sendStatus(E_CREATED);  
    else
        res.sendStatus(E_ALREADY_EXIST);  
 });

app.post('/devices/register', function(req, res) {
    console.log(req.body);
    doPOST(
        'http://' + REMOTE_ENDPOINT.IP + ':' +REMOTE_ENDPOINT.PORT + '/devices/register',
        req.body,
        function(error, response, respBody) {
            console.log(respBody);
            res.sendStatus(E_OK); 
        }
    )
 });

 app.post('/device/:dev/data', function(req, res) {
    console.log(req.body);
    var dev = req.params.dev;
    doPOST(
        'http://' + REMOTE_ENDPOINT.IP + ':' +REMOTE_ENDPOINT.PORT + '/device/' + dev + '/data',
        req.body,
        function(error, response, respBody) {
            console.log(respBody);
            res.sendStatus(E_OK); 
        }
    )
});
app.get('/gateways', function(req, res) {
    console.log(req.body);
    let resObj = [];
    db.gateways.forEach((v,k) => {
        resObj.push(v);
    });
    res.send(resObj);
});
app.get('/gateway/:gw', function(req, res) {
    console.log(req.body);
    var gw = req.params.gw;
    var gateway = db.gateways.get(gw);
    if (gateway)
        register();
        app.listen(LOCAL_ENDPOINT.PORT , function () {
            console.log(LOCAL_ENDPOINT.NAME + ' listening on : ' + LOCAL_ENDPOINT.PORT );
        });
        res.status(E_OK).send(JSON.stringify(gateway));
    else
        res.sendStatus(E_NOT_FOUND);
});

app.get('/ping', function(req, res) {
    console.log(req.body);
    res.status(E_OK).send({pong: Date.now()});
});

app.get('/health', function(req, res) {
    console.log(req.body);
    si.currentLoad((d) => {
        console.log(d);
        res.status(E_OK).send(JSON.stringify(d));
    })
});



//FROM HERE ON, THE CHAT GPT THING
let previousPacket = null;

app.post('/reducePacketFlow', async (req, res) => {
    try {
        const currentPacket = req.body;

        if (!currentPacket || typeof currentPacket.Data !== 'number') {
            return res.status(400).send('Invalid packet format');
        }

        // Calculate the mean if a previous packet exists
        if (previousPacket) {
            const meanData = (previousPacket.Data + currentPacket.Data) / 2;

            const newPacket = {
                Name: currentPacket.Name,
                Data: meanData,
                CreationTime: Date.now(),
                ReceptionTime: null,
            };
            axios
            // Forward the new packet to the next service
            try {
                await axios.post('http://service-b.<namespace>.svc.cluster.local/process', newPacket);
                console.log('Forwarded packet:', newPacket);
            } catch (error) {
                console.error('Error forwarding packet:', error.message);
            }
        }

        // Store the current packet for the next calculation
        previousPacket = currentPacket;

        res.status(200).send('Packet processed');
    } catch (error) {
        console.error('Error processing packet:', error.message);
        res.status(500).send('Internal server error');
    }
});


app.listen(LOCAL_ENDPOINT.PORT , function () {
    console.log(LOCAL_ENDPOINT.NAME + ' listening on : ' + LOCAL_ENDPOINT.PORT );
});