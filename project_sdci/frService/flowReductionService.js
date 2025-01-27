/**
 *  Author: Emilie Greaker greaker@insa-toulouse.fr
 *  Author: Y-Quynh Nguyen yqnguyen@insa-toulouse.fr
 *  File : saturationService.js
 *  Version : 0.1.0
 */

var express = require('express')
var app = express()
app.use(express.json())
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
    doPOST(
        'http://' + REMOTE_ENDPOINT.IP + ':' +REMOTE_ENDPOINT.PORT + '/gateways/register',
        req.body,
        function(error, response, respBody) {
            console.log(respBody);
            res.sendStatus(E_OK); 
        }
    )
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
    console.log('Fetching gateways from remote endpoint');

    const remoteUrl = `http://${REMOTE_ENDPOINT.IP}:${REMOTE_ENDPOINT.PORT}/gateways`;

    return request.get(remoteUrl, function(error, response, body) {
        if (error) {
            console.error('Error fetching gateways:', error);
            res.status(500).send('Error connecting to remote server');
            return;
        }
        
        console.log('Response from remote:', body);
        res.status(response.statusCode).send(body);
    });
});

// GET method: returns a specific gateway
app.get('/gateway/:gw', function(req, res) {
    console.log(req.body);
    var gw = req.params.gw;

    const remoteUrl = `http://${REMOTE_ENDPOINT.IP}:${REMOTE_ENDPOINT.PORT}/gateways/`+ gw;

    return request.get(remoteUrl, function(error, response, body) {
        if (error) {
            console.error('Error fetching gateways:', error);
            res.status(500).send('Error connecting to remote server');
            return;
        }
        
        console.log('Response from remote:', body);
        res.status(response.statusCode).send(body);
    });

});

app.listen(LOCAL_ENDPOINT.PORT , function () {
    console.log(LOCAL_ENDPOINT.NAME + ' listening on : ' + LOCAL_ENDPOINT.PORT );
});