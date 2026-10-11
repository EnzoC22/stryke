import { PeerServer } from 'peer';

const server = PeerServer({
  port: 9000,
  path: '/peer',
  key: 'peerjs',
  allow_discovery: false,
  proxied: false,
});

server.on('connection', (client) => {
  console.log('V441 PEER CONNECTED', client.getId());
});
server.on('disconnect', (client) => {
  console.log('V441 PEER DISCONNECTED', client.getId());
});
console.log('V441 LOCAL SIGNALING READY on 127.0.0.1:9000');
