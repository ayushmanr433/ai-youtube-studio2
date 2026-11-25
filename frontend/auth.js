import app from "./firebase.js";

import {
    getAuth,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    sendPasswordResetEmail,
    onAuthStateChanged,
    signOut
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";

const auth = getAuth(app);

// Create login interface
document.body.insertAdjacentHTML("beforeend", `
<style>
#auth-screen {
    position: fixed;
    inset: 0;
    z-index: 99999;
    background: #090b18;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: Arial, sans-serif;
}
.auth-card {
    width: 360px;
    max-width: 90%;
    padding: 35px;
    background: #171b35;
    border: 1px solid #454078;
    border-radius: 20px;
    color: white;
    box-shadow: 0 20px 60px #0008;
}
.auth-card h1 {
    text-align: center;
    color: #a78bfa;
}
.auth-card p {
    text-align: center;
    color: #aaa;
}
.auth-card input {
    width: 100%;
    box-sizing: border-box;
    padding: 13px;
    margin: 10px 0;
    border: 1px solid #454078;
    border-radius: 9px;
    background: #252a49;
    color: white;
}
.auth-card button {
    width: 100%;
    padding: 13px;
    margin-top: 12px;
    border: none;
    border-radius: 9px;
    background: #7955e9;
    color: white;
    font-weight: bold;
    cursor: pointer;
}
.auth-card button:hover {
    background: #9475ff;
}
.auth-link {
    color: #b49aff;
    cursor: pointer;
    text-align: center;
    margin-top: 18px;
}
#auth-message {
    color: #ff8585;
    font-size: 13px;
    text-align: center;
    margin-top: 12px;
}
#auth-logout {
    position: fixed;
    top: 15px;
    right: 20px;
    z-index: 100000;
    padding: 10px 18px;
    background: #7955e9;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
}
</style>

<div id="auth-screen">
    <div class="auth-card">
        <h1>AYUX STUDIO</h1>
        <p id="auth-subtitle">Welcome back! Sign in to continue.</p>

        <form id="auth-form">

            <input
                id="auth-name"
                type="text"
                placeholder="Your full name"
                style="display:none"
            >

            <input
                id="auth-email"
                type="email"
                placeholder="Email address"
                required
            >

            <input
                id="auth-password"
                type="password"
                placeholder="Password"
                required
            >

            <button id="auth-submit" type="submit">
                Login
            </button>

        </form>

        <div id="auth-message"></div>

        <div class="auth-link" id="auth-toggle">
            New here? Create an account
        </div>

        <div class="auth-link" id="auth-forgot">
            Forgot password?
        </div>
    </div>
</div>
`);

let signupMode = false;

const form = document.getElementById("auth-form");
const nameInput = document.getElementById("auth-name");
const emailInput = document.getElementById("auth-email");
const passwordInput = document.getElementById("auth-password");
const message = document.getElementById("auth-message");
const submit = document.getElementById("auth-submit");
const subtitle = document.getElementById("auth-subtitle");
const toggle = document.getElementById("auth-toggle");

toggle.onclick = () => {
    signupMode = !signupMode;

    nameInput.style.display = signupMode ? "block" : "none";

    submit.textContent = signupMode ? "Create Account" : "Login";

    subtitle.textContent = signupMode
        ? "Create your AYUX STUDIO account"
        : "Welcome back! Sign in to continue.";

    toggle.textContent = signupMode
        ? "Already have an account? Login"
        : "New here? Create an account";

    message.textContent = "";
};

form.onsubmit = async (event) => {
    event.preventDefault();

    message.textContent = "Please wait...";

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    try {
        if (signupMode) {
            await createUserWithEmailAndPassword(
                auth,
                email,
                password
            );
        } else {
            await signInWithEmailAndPassword(
                auth,
                email,
                password
            );
        }

        message.textContent = "";

    } catch (error) {
        message.textContent = error.message;
    }
};

// Forgot password
document.getElementById("auth-forgot").onclick = async () => {
    const email = emailInput.value.trim();

    if (!email) {
        message.textContent = "Enter your email address first.";
        return;
    }

    try {
        await sendPasswordResetEmail(auth, email);
        message.textContent = "Password reset email sent!";
    } catch (error) {
        message.textContent = error.message;
    }
};

// Monitor login status
onAuthStateChanged(auth, (user) => {
    const screen = document.getElementById("auth-screen");

    if (user) {
        screen.style.display = "none";

        if (!document.getElementById("auth-logout")) {
            const logout = document.createElement("button");

            logout.id = "auth-logout";
            logout.textContent = "Logout";

            logout.onclick = async () => {
                await signOut(auth);
            };

            document.body.appendChild(logout);
        }
    } else {
        screen.style.display = "flex";

        document.getElementById("auth-logout")?.remove();
    }
});

console.log("AYUX STUDIO Authentication loaded!");