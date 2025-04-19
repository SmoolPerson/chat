socket = new WebSocket("ws://localhost:5001");
let recipient = "everyone";
let dmlist = []

socket.addEventListener('open', function(event) {
    // this is a special message handled by the server to load initial messages
    let authToken = document.cookie.split('=')[1]
    socket.send("loadmsg" + JSON.stringify({authToken: authToken, recipient: "everyone"}));
    socket.send("initdm" + JSON.stringify({authToken: authToken}));
});

// just add nodes to the chatdiv
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
        const element = document.getElementById("chatdiv");
        for (let i = element.children.length - 1; i >= 0; i--) {
            element.children[i].remove();
        }
        for (let i = 0; i < initdata.length; i++) {
            let node = initdata[i]["username"] + ": " + initdata[i]["message"];
            update_message_list(node)
        }
    }

    else if (event.data.substring(0, 6) == "initdm") {
        dmdata = JSON.parse(event.data.replace("initdm", ""))
        console.log(dmdata);
        const dmdiv = document.getElementById("dmdiv");
        for (let i = 0; i < dmdata.length; i++) {
            const button = document.createElement("button");
            button.setAttribute("class", "dmbutton");
            button.setAttribute("onclick", "load(this.innerHTML)")
            button.innerHTML = dmdata[i]
            dmdiv.appendChild(button);
        }
        dmlist = dmdata;
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
        if (recipient == message["intendedreceiver"]) {
            update_message_list(message["username"] + ": " + message["message"]);
        }
        else {
            update_message_list("Received Message From: " + message["username"]);
        }
        if (dmlist.indexOf(message["username"]) == -1 && message["recipient"] != "everyone" && message["username"] != ) {
            const dmdiv = document.getElementById("dmdiv");
            const button = document.createElement("button");
            button.setAttribute("class", "dmbutton");
            button.setAttribute("onclick", "load(this.innerHTML)")
            button.innerHTML = message["username"]
            dmdiv.appendChild(button);
            dmlist.push(message["username"])
            console.log(dmlist)
        }
    }
    else {
        // notify user if the cookie is incorrect
        update_message_list("An error occurred with authentication. Please try logging in again or clearing your cookies.");
    }
}; 

// send an individual message to the server
function send(){
    let authToken = document.cookie.split('=')[1]
    const chatrecip = document.getElementById("chatrecip")
    console.log(recipient);
    if (recipient != chatrecip.value) {
        load(chatrecip.value);
    }
    let jsonMessage = {"authToken": authToken, "message": document.getElementById("chatsend").value, "recipient": recipient};
    console.log(JSON.stringify(jsonMessage));
    socket.send(JSON.stringify(jsonMessage));
    document.getElementById("chatsend").value = ""
}

function backToLogin(event) {
    // reset cookie so user doesnt login immediately again
    document.cookie = "authCookie=;"

    window.location.href = event.target.href
}

document.addEventListener("keypress", function onEvent(event) {
    if (event.key == "Enter") {
        send();
    }
});

function load(person) {
    let authToken = document.cookie.split('=')[1]
    const textarea = document.getElementById("chatrecip")
    if (recipient != person) {
        recipient = person
        textarea.value = person;
        socket.send("loadmsg" + JSON.stringify({authToken: authToken, recipient: recipient}));
    }

}