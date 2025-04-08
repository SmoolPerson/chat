socket = new WebSocket("ws://192.168.1.242:5001");


socket.addEventListener('open', function(event) {
    socket.send("loadmsg");
});

socket.onmessage = function(event) {
    const para = document.createElement("p");
    let node;
    if (event.data.substring(0, 5) == "init ") {
        initdata = JSON.parse(event.data.replace("init ", ""))
        console.log(initdata)
        for (let i = 0; i < initdata.length; i++) {
            const para = document.createElement("p");
            let node = document.createTextNode(initdata[i]["username"] + ": " + initdata[i]["message"]);
            para.appendChild(node);
            const element = document.getElementById("chatdiv");
            element.appendChild(para);
        }
        return;
    }
    else if (event.data != 'invalidCookieError') {
    let message = JSON.parse(event.data);
        node = document.createTextNode(message["username"] + ": " + message["message"]);
    }
    else {
        node = document.createTextNode("An error occurred with authentication. Please try logging in again.");
    }
    para.appendChild(node);
    const element = document.getElementById("chatdiv");
    element.appendChild(para);
    element.children[0].remove();
};

function send(){
    let authToken = document.cookie.split('=')[1]
    let jsonMessage = {"authToken": authToken, "message": document.getElementById("chatsend").value}
    socket.send(JSON.stringify(jsonMessage));
    document.getElementById("chatsend").value = ""
}

document.addEventListener("keypress", function onEvent(event) {
    if (event.key === "Enter") {
        send()
    }
});