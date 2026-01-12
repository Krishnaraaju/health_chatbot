# 🚀 Swasthya Sahayak: Future Roadmap

This document outlines strategic enhancements for the next phase of development, focusing on accessibility, reach, and scalability while maintaining the strict non-diagnostic scope (Problem ID: 25049).

## 1. Accessibility Enhancements (High Priority)
### 🎙️ Voice Interaction (Text-to-Speech)
*   **Goal**: Allow illiterate or elderly users to "listen" to health advice.
*   **Implementation**: Use the Web Speech API (`window.speechSynthesis`) to read out the chatbot's responses in the selected language.
*   **Benefit**: Massive increase in accessibility for rural populations.

### 📶 Offline Mode (PWA)
*   **Goal**: Allow access to basic content (Vaccination Schedules, Static First Aid) without internet.
*   **Implementation**: Convert the web app to a Progressive Web App (PWA) with Service Workers caching the `MasterData/` content.

## 2. Platform Expansion
### 📲 WhatsApp Integration (Twilio)
*   **Goal**: Reach users where they already are.
*   **Current State**: Simulated mode exists.
*   **Next Step**: Connect `app.py` to Twilio Sandbox API.
*   **Benefit**: True "zero-install" access for users.

## 3. Data & Analytics
### 📊 Geo-Spatial Disease Mapping
*   **Goal**: Visualize outbreak hotspots on a map.
*   **Implementation**: When users ask about symptoms, log their approximate location (IP-based or self-reported District) to a heatmap on the Admin Portal.
*   **Note**: Strictly anonymous; aggregated data only.

## 4. Content Expansion
### 📹 Video Content Integration
*   **Goal**: Visual learning.
*   **Implementation**: When a user asks about "CPR" or "Handwashing", embed a curated YouTube video or GIF in the chat response.

---

## 🎓 Viva Talking Points (Why these matter)
*   "We focused on **Multilingual Text** first to ensure accuracy, but **Voice** is our immediate next step for rural accessibility."
*   "The system is designed to be **Channel Agnostic**—the backend can serve Web, WhatsApp, or SMS equally well."
