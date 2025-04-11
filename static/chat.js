socket = new WebSocket("ws://localhost:5001");

socket.addEventListener('open', function(event) {
    // this is a special message handled by the server to load initial messages
    socket.send("loadmsg");
});

// just add notes to the chatdiv
function update_message_list(message) {
    const para = document.createElement("p")
    const node = document.createTextNode(message)
    para.appendChild(node);
    const element = document.getElementById("chatdiv");
    element.appendChild(para);
    if (element.children.length > 50) {
        element.children[0].remove();
    }
    element.scrollTop = element.scrollHeight;
}

socket.onmessage = function(event) {
    console.log(event.data)
    if (event.data.substring(0, 5) == "init ") {
        initdata = JSON.parse(event.data.replace("init ", ""))
        // loop through json data to add it to div
        for (let i = 0; i < initdata.length; i++) {
            let node = initdata[i]["username"] + ": " + initdata[i]["message"];
            update_message_list(node)
        }
    }
    // update number of people online
    else if (event.data.substring(0, 5) == "peopl") {
        value = event.data.substring(12);
        const para = document.getElementById("onlinepeople")
        para.innerHTML = "People online: " + value
    }
    else if (event.data != 'invalidCookieError') {
        // add individual message
        let message = JSON.parse(event.data);
        update_message_list(message["username"] + ": " + message["message"]);
    }
    else {
        // notify user if the cookie is incorrect
        update_message_list("An error occurred with authentication. Please try logging in again or clearing your cookies.");
    }
}; 

// send an individual message to the server
function send(){
    let authToken = document.cookie.split('=')[1]
    let jsonMessage = {"authToken": authToken, "message": document.getElementById("chatsend").value}
    socket.send(JSON.stringify(jsonMessage));
    document.getElementById("chatsend").value = ""
}

function backToLogin(event) {
    // reset cookie so user doesnt login immediately again
    document.cookie = "authCookie=;"

    window.location.href = event.target.href
}

document.addEventListener("keypress", function onEvent(event) {
    if (event.key === "Enter") {
        let authToken = document.cookie.split('=')[1]
    let jsonMessage = {"authToken": authToken, "message": document.getElementById("chatsend").value}
    socket.send(JSON.stringify(jsonMessage));
    document.getElementById("chatsend").value = ""
    }
});
