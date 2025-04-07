socket = new WebSocket("ws://127.0.0.1:5001");
socket.onmessage = function(event) {
    console.log('Received message from server: ' + event.data);
};
function send(){
    authToken = document.cookie.split('=')[1]
    jsonMessage = {"authToken": authToken, "message": document.getElementById("chatsend").value}
    socket.send(JSON.stringify(jsonMessage));
}