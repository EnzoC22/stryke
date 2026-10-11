import express from 'express';
import { createServer } from 'node:http';
import { ExpressPeerServer } from 'peer';

// Test-only HTTP server: serves the checked-in game and PeerJS from one origin.
// This prevents browser Private Network Access/CORS restrictions from affecting
// the integration test. The production network endpoints are untouched.
const app = express();
const http = createServer(app);
const signaling = ExpressPeerServer(http, { allow_discovery: false, proxied: false });
app.use('/peer', signaling);
app.use(express.static(process.cwd(), { index: 'index.html' }));

signaling.on('connection', client => console.log('V441 PEER CONNECTED', client.getId()));
signaling.on('disconnect', client => console.log('V441 PEER DISCONNECTED', client.getId()));

http.listen(9000, '127.0.0.1', () => {
  console.log('V441 SAME-ORIGIN STRYKE AND PEERJS READY ON http://127.0.0.1:9000/');
});
