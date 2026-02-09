const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const chat = document.getElementById("chat");

const SERVER_URL = "http://192.168.2.142:8000/process";

async function setRemoteMode() {
    try {
        await fetch("http://192.168.2.142:8000/set_mode/remote", { method: "POST" });
        console.log("Remote mode enabled");
    } catch (e) {
        console.log("Retrying remote mode...");
        setTimeout(setRemoteMode, 1000);
    }
}

setRemoteMode();



function addMessage(text, isUser) {
    const div = document.createElement("div");
    div.className = "message " + (isUser ? "user" : "bot");
    div.textContent = text;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, true);
    input.value = "";

    try {
        const response = await fetch(SERVER_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });

        const data = await response.json();
        if (data.reply) {
            addMessage(data.reply, false);
        }
    } catch (err) {
        addMessage("Error connecting to server.", false);
    }
}

sendBtn.addEventListener("click", sendMessage);
input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
});
