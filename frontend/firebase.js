// Import Firebase
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";

// Firebase configuration for AYUX STUDIO
const firebaseConfig = {
    apiKey: "AIzaSyD2tKPKnqhOYG2s8ibiwgJATxAVySQBCA8",
    authDomain: "ayux-studio-5.firebaseapp.com",
    projectId: "ayux-studio-5",
    storageBucket: "ayux-studio-5.firebasestorage.app",
    messagingSenderId: "893929649617",
    appId: "1:893929649617:web:ea944dc18ef69c3dcd9cf0",
    measurementId: "G-L0LNC5HD34"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Export Firebase app
export default app;

console.log("AYUX STUDIO Firebase connected successfully!");