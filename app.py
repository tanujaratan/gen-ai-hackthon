# app.py — complete Streamlit mental-wellness assistant with game
import streamlit as st
import json
from datetime import datetime
import matplotlib.pyplot as plt
import traceback
import random

# Use the google.generativeai client
import google.generativeai as genai

# ---------------- CONFIG ----------------
API_KEY = "AIzaSyDfnvI-s57IWtU4n6ffX6Se3BuZsjs1KzA"  # <<< REPLACE with valid Gemini API key
genai.configure(api_key=API_KEY)

SYSTEM_INSTRUCTION = (
    "You are a youth mental-wellness assistant. Always respond in an empathetic, "
    "non-judgmental tone. Keep responses short (1-3 sentences) unless user asks for more. "
)

HISTORY_FILE = "mood_history.json"

WHO5 = [
    "Over the last two weeks I have felt cheerful and in good spirits.",
    "Over the last two weeks I have felt calm and relaxed.",
    "Over the last two weeks I have felt active and vigorous.",
    "Over the last two weeks I woke up feeling fresh and rested.",
    "Over the last two weeks my daily life has been filled with things that interest me."
]

MOOD_QUESTIONS = ["Happiness", "Calmness", "Energy", "Freshness", "Enjoyment"]

SAFE_HELPLINES = [
    {"name": "Tele-MANAS (India)", "number": "14416 / 1800-891-4416", "note": "24/7 free mental-health support."},
    {"name": "KIRAN (India Rehab helpline)", "number": "1800-599-0019", "note": "24/7 mental health rehab."},
    {"name": "iCALL (TISS)", "number": "022-25521111 / 9152987821", "note": "telephone & email counseling."}
]

CRITICAL_KEYWORDS = ["suicide", "kill myself", "want to die", "end my life", "hurt myself", "cant go on", "can't go on"]
SAD_KEYWORDS = ["sad", "unhappy", "depressed", "low", "down"]

EXERCISES = [
    "Try 4-4-6 breathing: inhale 4s, hold 4s, exhale 6s — repeat 6 times.",
    "Take a 5-minute mindful walk, noticing your surroundings slowly.",
    "Grounding: name 5 things you can see, 4 things you can feel, 3 things you can hear."
]

JOKES = [
    "Why don’t skeletons fight each other? They don’t have the guts!",
    "I told my computer I needed a break — it sent me a Kit-Kat.",
    "Why did the math book look sad? Because it had too many problems."
]

# Guess-the-word game
GAME_QUESTIONS = [
    {"q": "I am round and often seen in the sky at night. What am I?", "a": "moon"},
    {"q": "I have keys but no locks. What am I?", "a": "piano"},
    {"q": "I can fly without wings and cry without eyes. What am I?", "a": "cloud"},
    {"q": "I am the largest land animal. What am I?", "a": "elephant"},
    {"q": "I have a neck but no head. What am I?", "a": "bottle"}
]

# ---------------- Utility ----------------
def read_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def append_history(entry):
    hist = read_history()
    hist.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2, ensure_ascii=False)

def is_critical(text: str):
    lower = (text or "").lower()
    return any(k in lower for k in CRITICAL_KEYWORDS)

def show_helplines():
    st.error("If you are in immediate danger, please call local emergency services right now.")
    st.markdown("**Trusted helplines:**")
    for h in SAFE_HELPLINES:
        st.markdown(f"- **{h['name']}**: {h['number']} — {h['note']}")

def extract_text_from_response(resp):
    try:
        if getattr(resp, "generations", None):
            g = resp.generations[0]
            if getattr(g, "text", None):
                return g.text
            if getattr(g, "content", None):
                return getattr(g.content, "text", None) or str(g.content)
    except Exception:
        pass
    try:
        if getattr(resp, "candidates", None):
            cand = resp.candidates[0]
            cont = getattr(cand, "content", None)
            if cont and getattr(cont, "parts", None):
                part = cont.parts[0]
                if getattr(part, "text", None):
                    return part.text
    except Exception:
        pass
    return getattr(resp, "text", None)

def call_gemini(prompt: str, model_name="gemini-1.5-flash"):
    try:
        model = genai.GenerativeModel(model_name)
        resp = model.generate_content(prompt)
        text = extract_text_from_response(resp)
        if not text:
            text = str(resp)
        return text, None
    except Exception as e:
        tb = traceback.format_exc()
        return None, str(e) + "\n" + tb

def get_gemini_reply(user_text):
    if not user_text or not user_text.strip():
        return "Please type something for me to help with."
    if is_critical(user_text):
        return None
    prompt = SYSTEM_INSTRUCTION + "\nUser: " + user_text + "\nAssistant:"
    reply, err = call_gemini(prompt)
    if err:
        return None
    return reply

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Youth Mental Wellness Assistant", layout="centered")
st.title("Youth Mental Wellness Assistant")

page = st.sidebar.radio("Choose a feature", ["Chat", "WHO-5 Questionnaire", "Mood Tracker", "Helplines / Tips", "History", "Guess-the-Word Game"])

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "game_round" not in st.session_state:
    st.session_state.game_round = 0

if page == "Chat":
    st.header("Chat with the wellness assistant (text only)")
    if st.session_state.chat_history:
        for role, msg in st.session_state.chat_history:
            if role == "You":
                st.markdown(f"**You:** {msg}")
            else:
                st.markdown(f"**Bot:** {msg}")

    user_input = st.text_input("Type your message here", key="chat_input")
    send = st.button("Send")

    if send:
        text = (user_input or "").strip()
        if not text:
            st.warning("Please type a message before sending.")
        else:
            st.session_state.chat_history.append(("You", text))
            if is_critical(text):
                st.session_state.chat_history.append(("Bot", "I'm worried you mentioned something serious. Please contact emergency services or one of these helplines immediately."))
                show_helplines()
            elif any(k in text.lower() for k in SAD_KEYWORDS):
                joke = random.choice(JOKES)
                exercise = random.choice(EXERCISES)
                st.session_state.chat_history.append(("Bot", f"💡 Exercise: {exercise}\n😂 Joke: {joke}"))
            else:
                reply = get_gemini_reply(text)
                if reply is None:
                    st.error("Temporary Chatbot error or API unreachable. Showing fallback response.")
                    fallback = "I'm having trouble connecting to my helper right now. Can I suggest a breathing exercise? Try: breathe in for 4, hold 4, out 6."
                    st.session_state.chat_history.append(("Bot", fallback))
                else:
                    st.session_state.chat_history.append(("Bot", reply))
    st.markdown("---")
    st.info("Tip: Ask about mood check-ins, exercises, or just say how your day was.")

elif page == "WHO-5 Questionnaire":
    st.header("WHO-5 Wellbeing Questionnaire")
    st.write("Answer each question from 0 (At no time) to 5 (All the time).")
    answers = []
    for i, q in enumerate(WHO5):
        val = st.number_input(q, min_value=0, max_value=5, step=1, key=f"who5_{i}")
        answers.append(int(val))
    if st.button("Submit WHO-5"):
        raw = sum(answers)
        percent = raw * 4
        entry = {"ts": datetime.utcnow().isoformat(), "type": "WHO5", "raw": raw, "percent": percent, "answers": answers}
        append_history(entry)
        if percent < 50:
            st.warning(f"Your WHO-5 score is {percent}/100 — this is a low score. Consider seeking support.")
            show_helplines()
        else:
            st.success(f"Your WHO-5 score is {percent}/100 — looks okay. Keep practicing self-care.")
        st.write("Saved your WHO-5 entry.")

elif page == "Mood Tracker":
    st.header("Daily Mood Tracker (1-5 scale)")
    st.write("Rate each mood for today (1 = very low, 5 = high).")
    mood_answers = {}
    for i, m in enumerate(MOOD_QUESTIONS):
        mood_answers[m] = st.slider(m, 1, 5, 3, key=f"mood_{i}")
    if st.button("Save Today's Mood"):
        today_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = {"ts": today_str, "type": "Mood", "answers": mood_answers}
        append_history(entry)
        st.success(f"Saved today's mood ({today_str}).")
        fig, ax = plt.subplots()
        ax.bar(list(mood_answers.keys()), list(mood_answers.values()))
        ax.set_ylim(0, 5)
        ax.set_ylabel("Score (1-5)")
        ax.set_title("Today's Mood Scores")
        plt.xticks(rotation=15)
        st.pyplot(fig)

elif page == "Helplines / Tips":
    st.header("Helplines & Quick Tips")
    st.markdown("If you are in immediate danger, call your local emergency number right now.")
    show_helplines()
    st.markdown("---")
    st.subheader("Quick coping suggestions")
    st.markdown(
        "- Try 4-4-6 breathing (inhale 4s, hold 4s, exhale 6s) for 2 minutes.\n"
        "- 5-minute mindful walk.\n"
        "- Grounding: name 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste.\n"
    )

elif page == "History":
    st.header("Saved History (WHO-5 & Mood)")
    hist = read_history()
    if not hist:
        st.info("No history saved yet.")
    else:
        for e in reversed(hist[-50:]):
            t = e.get("ts", "")
            typ = e.get("type", "")
            if typ == "WHO5":
                st.markdown(f"- WHO-5 @ {t}: score {e.get('percent')} /100")
            elif typ == "Mood":
                st.markdown(f"- Mood @ {t}: " + ", ".join([f"{k}:{v}" for k, v in e.get("answers", {}).items()]))
            else:
                st.markdown(f"- {typ} @ {t}: {e}")




elif page == "Guess-the-Word Game":
    st.header("Guess-the-Word Challenge")

# Initialize session state variables
    if "game_round" not in st.session_state:
       st.session_state.game_round = 0
    if "played" not in st.session_state:
       st.session_state.played = False
    st.header("Guess-the-Word Challenge")
    if "game_round" not in st.session_state or st.session_state.game_round >= len(GAME_QUESTIONS):
        st.session_state.game_round = 0
        st.session_state.played = False

    if not st.session_state.played:
        q_obj = GAME_QUESTIONS[st.session_state.game_round]
        st.markdown(f"**Question {st.session_state.game_round+1}:** {q_obj['q']}")
        user_guess = st.text_input("Your guess:", key=f"guess_{st.session_state.game_round}")
        submit_guess = st.button("Submit Guess")

        if submit_guess:
            if user_guess.strip().lower() == q_obj["a"].lower():
                st.success("Correct! ✅")
            else:
                st.warning(f"Wrong! The correct answer is: {q_obj['a']}")
            st.session_state.played = True
    else:
        next_btn = st.button("Next Question")
        if next_btn:
            st.session_state.game_round += 1
            st.session_state.played = False
        elif st.session_state.game_round == len(GAME_QUESTIONS)-1:
            st.button("Play Again?", on_click=lambda: st.session_state.update({"game_round":0, "played":False}))

st.markdown("---")
st.markdown("Built for a hackathon demo. Data is stored locally in `mood_history.json`.")
