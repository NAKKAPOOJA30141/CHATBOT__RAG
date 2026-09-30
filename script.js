const input = document.getElementById("questionInput");
const sendButton = document.getElementById("sendButton");
const chatArea = document.getElementById("chatArea");


// ==========================================
// SEND QUESTION
// ==========================================

async function sendQuestion() {

    const question = input.value.trim();

    if (question === "") {
        return;
    }


    // Remove welcome screen
    const welcome = document.querySelector(".welcome");

    if (welcome) {
        welcome.remove();
    }


    // Show user's message
    addMessage(
        question,
        "user"
    );


    // Clear input
    input.value = "";


    // Disable button
    sendButton.disabled = true;


    // Show typing
    const typingMessage = addTyping();


    try {

        const response = await fetch(
            "/ask",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    question: question
                })
            }
        );


        const data = await response.json();


        // Remove typing indicator
        typingMessage.remove();


        // Show bot answer
        addMessage(
            data.answer,
            "bot"
        );


    } catch (error) {

        typingMessage.remove();

        addMessage(
            "Sorry, something went wrong. Please check whether the Flask server is running.",
            "bot"
        );

        console.error(error);

    }


    // Enable button
    sendButton.disabled = false;

    input.focus();

}


// ==========================================
// ADD MESSAGE
// ==========================================

function addMessage(text, sender) {

    const message = document.createElement("div");

    message.className =
        "message " + sender;


    const avatar = document.createElement("div");

    avatar.className = "avatar";

    avatar.textContent =
        sender === "user" ? "👤" : "🤖";


    const bubble = document.createElement("div");

    bubble.className = "bubble";

    bubble.textContent = text;


    message.appendChild(avatar);

    message.appendChild(bubble);


    chatArea.appendChild(message);


    scrollToBottom();

}


// ==========================================
// TYPING INDICATOR
// ==========================================

function addTyping() {

    const message = document.createElement("div");

    message.className = "message bot";


    const avatar = document.createElement("div");

    avatar.className = "avatar";

    avatar.textContent = "🤖";


    const bubble = document.createElement("div");

    bubble.className = "bubble";


    const typing = document.createElement("div");

    typing.className = "typing";


    for (let i = 0; i < 3; i++) {

        const dot = document.createElement("span");

        typing.appendChild(dot);

    }


    bubble.appendChild(typing);

    message.appendChild(avatar);

    message.appendChild(bubble);

    chatArea.appendChild(message);


    scrollToBottom();


    return message;

}


// ==========================================
// SUGGESTION BUTTON
// ==========================================

function askSuggestion(question) {

    input.value = question;

    sendQuestion();

}


// ==========================================
// ENTER KEY
// ==========================================

input.addEventListener(
    "keydown",
    function(event) {

        if (event.key === "Enter") {

            event.preventDefault();

            sendQuestion();

        }

    }
);


// ==========================================
// SCROLL
// ==========================================

function scrollToBottom() {

    chatArea.scrollTop =
        chatArea.scrollHeight;

}