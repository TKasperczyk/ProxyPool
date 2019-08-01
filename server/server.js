//Requires the http-proxy module
//Usage: node server.js <port>

const httpProxy = require('http-proxy');
const http = require('http');
const url = require('url');
const net = require('net');

//Check if the port was supplied
const port = process.argv[2];
if (port === undefined) {
    console.error('You need to specify the TCP listen port');
    process.exit();
}

//Handles HTTP traffic
const server = http.createServer((req, res) => {
    const urlObj = url.parse(req.url);
    const target = `${urlObj.protocol}//${urlObj.host}`;
    console.log(`Proxy HTTP request for: ${target}`);

    const proxy = httpProxy.createProxyServer({});
    proxy.on('error', (err, req, res) => {
        console.error('Proxy error: ', err);
        res.end();
    });
    proxy.web(req, res, {
        target
    });
}).listen(port);
console.log(`Listening on ${port}`);

//Extract host information from the request url. If the port was included in the url, it will overwrite the default port
const getHostPortFromString = (hostString, defaultPort) => {
    let host = hostString;
    let port = defaultPort;

    const rgxResult = /^([^:]+)(:([0-9]+))?$/.exec(hostString);
    if (rgxResult != null) {
        host = rgxResult[1];
        if (rgxResult[2] != null) {
            port = rgxResult[3];
        }
    }
    return {host, port};
};

//Handles HTTPS traffic
server.addListener('connect', (req, socket, bodyhead) => {
    const hostPort = getHostPortFromString(req.url, 443);
    console.log(`Proxying an HTTPS request for: ${hostPort.host}:${hostPort.port}`);

    //Create a proxy connection and pass HTTP 200 to the socket
    const proxySocket = new net.Socket();
    proxySocket.connect(hostPort.port, hostPort.host, () => {
        proxySocket.write(bodyhead);
        socket.write('HTTP/' + req.httpVersion + ' 200 Connection established\r\n\r\n');
    });

    //Forward traffic coming from the outside
    proxySocket.on('data', (chunk) => { socket.write(chunk); });
    proxySocket.on('end', () => { socket.end(); });
    //Forward traffic coming from the inside
    socket.on('data', (chunk) => { proxySocket.write(chunk); });
    socket.on('end', () => { proxySocket.end(); });
    //Handle errors from both sides
    socket.on('error', () => {
        proxySocket.end(); //No need to write anything because it's just a middleman
    });
    proxySocket.on('error', () => {
        socket.write('HTTP/' + req.httpVersion + ' 500 Connection error\r\n\r\n'); //Inform the user that there was an error on the proxy's side
        socket.end();
    });
});
