//server.js
const express = require('express');
const { util } = require('util');
// Transforme exec en version basée sur les Promesses
const exec = require('util').promisify(require('child_process').exec);
const dotenv = require('dotenv');
dotenv.config({ path: './.env' });


const app = express();
const JETSON_IP_HOST = process.env.JETSON_IP_HOST;

// handling CORS
app.use((req, res, next) => {
    res.header("Access-Control-Allow-Origin", 
               "http://localhost:4200");
    res.header("Access-Control-Allow-Headers", 
               "Origin, X-Requested-With, Content-Type, Accept");
    next();
});

// route for hello word
app.get('/api/message', (req, res) => {
    res.send("HELLO WORLD !!!!");
});

app.get('/api/message', (req, res) => {
    res.send("HELLO WORLD !!!!");
});

app.get("/mila/start", async (req, res) => {
    try{
        const { stdout, stderr } = await exec(`mosquitto_pub -h ${JETSON_IP_HOST} -t mila/control -m start_main_script`);

        if (stderr) {
            throw new Error(stderr);
        }
        res.status(200).json({ success: true, output: "Mila START !!!! Yeah!!!" });
    }catch(error){
        res.status(500).send("Un problème est survenu");
    }
});

app.get("/mila/stop", async (req, res) => {
    try{
        const { stdout, stderr } = await exec(`mosquitto_pub -h ${JETSON_IP_HOST} -t mila/control -m stop_main_script`);

        if (stderr) {
            throw new Error(stderr);
        }
        res.status(200).json({ success: true, output: "Mila STOP!!! :(" });
    }catch(error){
        res.status(500).send("Un problème est survenu");
    }
});

app.listen(3000, () => {
    console.log('Server listening on port 3000');
});