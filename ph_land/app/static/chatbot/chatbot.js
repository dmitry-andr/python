const chat = document.getElementById("chat");

function append(sender, text, cls){

    const div = document.createElement("div");

    div.className = cls;

    div.innerHTML = "<b>" + sender + ":</b> " + text;

    chat.appendChild(div);

    chat.scrollTop = chat.scrollHeight;
}


async function sendMessage(){

    const input = document.getElementById("message");

    const message = input.value.trim();

    if(message==="")
        return;

    append("You", message, "user");

    input.value="";

    const response = await fetch("/chat-api/chat",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({
            message:message
        })
    });

    const data = await response.json();

    append("Bot", data.answer, "bot");
}