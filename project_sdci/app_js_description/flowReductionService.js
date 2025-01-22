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

// Database of the packages
var db_package = {
    packages : new Map()
};

// Add new package to database
function addNewPackage(pk) {
    var res = -1;
    if (!db_package.packages.get(pk.Name + "_package_1")) {
        db_package.packages.set(pk.Name + "_package_1", pk);
        res = 0;
    }
    else if (!db_package.packages.get(pk.Name + "_package_2")) {
        db_package.packages.set(pk.Name + "_package_2", pk);
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

    var result = addNewpackage(req.body);
    if (result === 0) {
        res.sendStatus(E_CREATED);  
    }
    else {
        // There are already two packages stored for this device

        // Get the two stored packages from the package db
        var package1 = db_package.packages.get(req.body.Name + "_package_1");
        var package2 = db_package.packages.get(req.body.Name + "_package_2");

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
        removePackage(package2.Name);

        // Add the incoming package to the package db
        var result = addNewpackage(req.body);
        if (result === 0) {
            res.sendStatus(E_CREATED);  
        }
        else {
            // If this happens at this point, there is something seriously wrong...
            res.sendStatus(E_ALREADY_EXIST); 
        }
    }
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