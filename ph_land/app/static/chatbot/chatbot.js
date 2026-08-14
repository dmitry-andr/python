const chat = document.getElementById("chat");
const input = document.getElementById('message');
const limitMsg = document.getElementById('limit-message');
const MAX_LENGTH = 100;

input.addEventListener('input', () => {
        if (input.value.length >= MAX_LENGTH) {
            input.value = input.value.slice(0, MAX_LENGTH);
            limitMsg.style.display = 'block';
        } else {
            limitMsg.style.display = 'none';
        }
    });

/*
*Chatbot functions
*/
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

    const savedSessionId = window.localStorage.getItem("chat_session_id");

    const response = await fetch("/chat-api/chat",{
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: message,
            session_id: savedSessionId,
        })
    });

    const data = await response.json();

    if (data.session_id) {
        window.localStorage.setItem("chat_session_id", data.session_id);
    }

    append("Bot", data.answer, "bot");
}