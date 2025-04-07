socket = new WebSocket("ws://127.0.0.1:5001");


socket.addEventListener('open', function(event) {
    socket.send("loadmsg");
});

socket.onmessage = function(event) {
    const para = document.createElement("p");
    let node;
    if (event.data != 'Invalid cookie. Try logging in again') {
    let message = JSON.parse(event.data);
        node = document.createTextNode(message["username"] + ": " + message["message"]);
    }
    else {
        node = document.createTextNode("An error occurred with authentication. Please try logging in again.");
    }
    para.appendChild(node);
    const element = document.getElementById("chatdiv");
    element.appendChild(para);
};

function send(){
    let authToken = document.cookie.split('=')[1]
    let jsonMessage = {"authToken": authToken, "message": document.getElementById("chatsend").value}
    socket.send(JSON.stringify(jsonMessage));
}