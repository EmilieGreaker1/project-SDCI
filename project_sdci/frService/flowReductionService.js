/**
 *  Author: Emilie Greaker greaker@insa-toulouse.fr
 *  Author: Y-Quynh Nguyen yqnguyen@insa-toulouse.fr
 *  File : saturationService.js
 *  Version : 0.1.0
 */

var express = require('express')
var app = express()
app.use(express.json()) // for parsing application/json
var request = require('request');
var argv = require('yargs').argv;

// Who we are and who we're sending too
var LOCAL_ENDPOINT = {IP : argv.local_ip, PORT : argv.local_port, NAME : argv.local_name};
var REMOTE_ENDPOINT = {IP : argv.remote_ip, PORT : argv.remote_port, NAME : argv.remote_name};

// HTTP STATUS
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

// Database of the packages
var db_package = {
    packages : new Map()
};

// Add new package to database
function addNewPackage(pk) {
    var res = -1;
    if (!db_package.packages.get(pk.Name)) {
        db_package.packages.set(pk.Name, pk);
        res = 0;
    }
    return res;
}

// Remove package from database
function removePackage(pk_name) {
    if (db_package.packages.get(pk_name))
        db_package.packages.delete(pk_name);
}
    
// Function to POST
function doPOST(uri, body, onResponse) {
    request({method: 'POST', uri: uri, json : body}, onResponse); 
}

// POST method: to register a gateway
app.post('/gateways/register', function(req, res) {
    console.log(req.body);
    var result = addNewGateway(req.body);
    if (result === 0)
        res.sendStatus(E_CREATED);  
    else
        res.sendStatus(E_ALREADY_EXIST);  
 });

// POST method: to register a device
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

// POST method: to treat incoming data, we send a package out of 2 with the mean value
 app.post('/device/:dev/data', function(req, res) {
    console.log(req.body);
    var dev = req.params.dev;

    var result = addNewPackage(req.body);
    if (result === 0) {
        res.sendStatus(E_CREATED);  
    }
    else {
        // There is already a package stored for this device

        // Get the two packages
        var package1 = db_package.packages.get(req.body.Name);
        var package2 = req.body;

        // Calculate the data mean of the two packages
        var meanData = (package1.Data + package2.Data) / 2;

        // Construct the new package
        const newpackageBody = {
            Name: req.body.Name,
            Data: meanData,
            CreationTime: package2.CreationTime,
            ReceptionTime: null,
        };

        // Send the new package to the remote endpoint (the GI) transparently from the device
        doPOST(
            'http://' + REMOTE_ENDPOINT.IP + ':' + REMOTE_ENDPOINT.PORT + '/device/' + dev + '/data',
            newpackageBody,
            function(error, response, respBody) {
                console.log(respBody);
                res.sendStatus(E_OK); 
            }
        )

        // Delete the previous two packages for this device
        removePackage(package1.Name);
    }
});

// GET method: returns the list of gateways
app.get('/gateways', function(req, res) {
    console.log(req.body);
    let resObj = [];
    db.gateways.forEach((v,k) => {
        resObj.push(v);
    });
    res.send(resObj);
});

// GET method: returns a specific gateway
app.get('/gateway/:gw', function(req, res) {
    console.log(req.body);
    var gw = req.params.gw;
    var gateway = db.gateways.get(gw);
    if (gateway) {
        register();
        app.listen(LOCAL_ENDPOINT.PORT , function () {
            console.log(LOCAL_ENDPOINT.NAME + ' listening on : ' + LOCAL_ENDPOINT.PORT );
        });
        res.status(E_OK).send(JSON.stringify(gateway));
    }
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

app.listen(LOCAL_ENDPOINT.PORT , function () {
    console.log(LOCAL_ENDPOINT.NAME + ' listening on : ' + LOCAL_ENDPOINT.PORT );
});