socket = new WebSocket("ws://localhost:5001");
let currentRecipient = "everyone";
let dmlist = new Set();
dmlist.add("everyone");

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
        // add initial direct message data to a list of direct messages, then display it using a helper function
        dmdata = JSON.parse(event.data.replace("initdm", ""))
        console.log(dmdata);
        for (i = 0; i < dmdata.length; i++) {
            dmlist.add(dmdata[i]);
        }
        displayDmlist(dmlist);
    }

    // update number of people online
    else if (event.data.substring(0, 5) == "peopl") {
        value = event.data.substring(12);
        const para = document.getElementById("onlinepeople")
        para.innerHTML = "People online: " + value
    }
    // if there is no authentication error
    else if (event.data != 'invalidCookieError') {
        let message = JSON.parse(event.data);
        
        // if the recipient of the current conversation is either the username or receiver, then the user is in current conversation
        if (currentRecipient == message["username"] || currentRecipient == message["intendedreceiver"]) {
            // display message since in current conversation
            update_message_list(message["username"] + ": " + message["message"]);
        }
        else {
            // display notif message since user is in different conversation
            update_message_list("Received Message From: " + message["username"]);
        }
        // we are going to add the message to the set of direct messages
        if (message["intendedreceiver"] != "everyone") {
            const name = document.getElementById("hello").innerHTML.replace(" Hello, ", "");
            // don't add the user's name to their dms, otherwise they would be sending a message to themself
            if (message["username"] != name) {
                dmlist.add(message["username"]);
            }
            if (message["intendedreceiver"] != name) {
                dmlist.add(message["intendedreceiver"]);
            }
            console.log(name)
            console.log(message["intendedreceiver"]);
            displayDmlist(dmlist);
        }
    }
    else {
        // notify user if the cookie is incorrect
        update_message_list("An error occurred with authentication. Please try logging in again or clearing your cookies.");
    }
}; 

function displayDmlist(dmdata) {
    // convert set to list
    let dmlist = [...dmdata];
    const element = document.getElementById("dmdiv");
    // loop backwards otherwise html is weird and deletes stuff
    for (let i = element.children.length - 1; i >= 0; i--) {
        element.children[i].remove();
    }
    for (let j = 0; j < dmlist.length; j++) {
        const button = document.createElement("button");
        button.setAttribute("class", "dmbutton");
        button.setAttribute("onclick", "load(this.innerHTML)")
        button.innerHTML = dmlist[j];
        element.appendChild(button);
    }
}

// send an individual message to the server
function send(){
    let authToken = document.cookie.split('=')[1];
    // get recipient
    const documentRecip = document.getElementById("chatrecip");
    console.log(currentRecipient);
    // need to load in the messages if user sends to someone else
    if (currentRecipient != documentRecip.value) {
        load(documentRecip.value);
    }
    let jsonMessage = {"authToken": authToken, "message": document.getElementById("chatsend").value, "recipient": currentRecipient};
    socket.send(JSON.stringify(jsonMessage));
    // reset text box for user's next message
    document.getElementById("chatsend").value = ""
}

function backToLogin(event) {
    // reset cookie so user doesnt login immediately again
    document.cookie = "authCookie=;"

    window.location.href = event.target.href
}

// supporting the enter key
document.addEventListener("keypress", function onEvent(event) {
    if (event.key == "Enter") {
        send();
    }
});

function load(person) {
    // make sure to trim the message so that user doesnt send to wrong user just because of whitespace
    person = person.trim();
    let authToken = document.cookie.split('=')[1];
    const textarea = document.getElementById("chatrecip");
    if (currentRecipient != person) {
        currentRecipient = person;
        textarea.value = person;
        socket.send("loadmsg" + JSON.stringify({authToken: authToken, "recipient": currentRecipient}));
    }

}