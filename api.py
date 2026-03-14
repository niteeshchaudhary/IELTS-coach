from fastapi import FastAPI, HTTPException, Depends, Header, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import uuid
import sqlite3
import hashlib
import os
import tempfile

# Load .env variables so config.py uses GROQ
from dotenv import load_dotenv
load_dotenv()

# Import intelligence engine
from intelligence.vocabulary import VocabularySystem
from engine.memory import ConversationMemory
from engine.conversation_state import ConversationStateMachine
from intelligence.llm_engine import get_llm
from intelligence.ielts_guidance import IELTSGuidance
from intelligence.ielts_scorer import IELTSScorer
from games import WordMatchingGame, SentenceCompletionGame, TypingSpeedGame, ErrorCorrectionGame
import config

# Initialize global users db
def init_users_db():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DATA_DIR / "users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT)''')
    conn.commit()
    conn.close()

init_users_db()

app = FastAPI(title="IELTS Coach API")

# Setup CORS for React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Removed global singleton instances to support multiple users
# We still need the state machine for basic status values
state_machine = ConversationStateMachine()

# In-memory storage for game sessions (since REST is stateless)
ACTIVE_GAMES = {} # session_id -> {"word_matching": instance, ...}

# Lazily loaded LLM
_llm = None

def get_api_llm():
    global _llm
    if _llm is None:
        _llm = get_llm()
    return _llm


# --- Pydantic Models ---
class SignupRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ChatMessage(BaseModel):
    message: str

class WordMatchCheck(BaseModel):
    answers: dict

class ListAnswersCheck(BaseModel):
    answers: list

class StringAnswerCheck(BaseModel):
    answer: str

# --- Helpers ---
def get_user_systems(username: str, session_id: str):
    """Instantiates memory systems for a specific user and session."""
    db_path = str(config.get_db_path(username))
    vocab_system = VocabularySystem(db_path=db_path)
    memory = ConversationMemory(db_path=db_path, session_id=session_id)
    return vocab_system, memory


# --- Endpoints ---
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@app.post("/api/signup")
def signup(req: SignupRequest):
    """Register a new user."""
    if not req.username.strip() or not req.password.strip():
        raise HTTPException(status_code=400, detail="Username and password cannot be empty")
        
    conn = sqlite3.connect(config.DATA_DIR / "users.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                  (req.username.strip(), hash_password(req.password)))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists. Please log in.")
    conn.close()
    return {"message": "Signup successful"}

@app.post("/api/login")
def login(req: LoginRequest):
    """Authenticate a user and provision a session_id."""
    conn = sqlite3.connect(config.DATA_DIR / "users.db")
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username=?", (req.username.strip(),))
    row = c.fetchone()
    conn.close()
    
    if not row or row[0] != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    session_id = f"sess_{req.username}_{int(time.time())}"
    
    # Initialize their database
    get_user_systems(req.username, session_id)
    
    return {
        "username": req.username,
        "session_id": session_id,
        "message": "Login successful"
    }


@app.get("/api/words")
def get_daily_words(username: str = Query(...), session_id: str = Query(...)):
    """Returns the daily words for the user."""
    vocab_system, memory = get_user_systems(username, session_id)
    words = vocab_system.get_daily_words()
    # Also log that they've seen them today, as the Streamlit app did
    memory.set_daily_vocab(vocab_system.get_daily_word_names())
    return {"words": words}


@app.get("/api/words/{word_id}")
def get_word(word_id: str, username: str = Query(...), session_id: str = Query(...)):
    """Gets a specific word. We iterate because the JSON structure is a list."""
    vocab_system, _ = get_user_systems(username, session_id)
    words = vocab_system._word_bank # Use the pre-loaded bank
    if words:
        for w in words:
             # create a pseudo ID since it may not exist in json
            pseudo_id = ''.join(filter(str.isalnum, w['word'].lower()))
            if pseudo_id == word_id or w['word'].lower() == word_id.lower():
                return w
                
    raise HTTPException(status_code=404, detail="Word not found")

@app.post("/api/chat")
def send_chat_message(req: ChatMessage, username: str = Query(...), session_id: str = Query(...)):
    """Sends a text message to the IELTS Coach and gets a text response."""
    from intelligence import prompts
    
    vocab_system, memory = get_user_systems(username, session_id)
    llm = get_api_llm()
    user_text = req.message
    
    # Simple logic mirror of Streamlit app.py (Part 1 Simulation)
    memory.add_turn("user", user_text)
    
    # 1. Get daily words for context
    daily_word_names = vocab_system.get_daily_word_names()
    
    # 2. Detect vocabulary usage
    from intelligence.vocab_detector import VocabDetector
    detector = VocabDetector()
    detector.set_llm(llm)
    vocab_results = detector.detect(user_text, daily_word_names)
    vocab_parts = []
    for word, result in vocab_results.items():
        if result["status"] != "NOT_USED":
            vocab_parts.append(f"{word}: {result['status']}")
            vocab_system.record_usage(word, result["status"] == "CORRECT")
    vocab_status = "; ".join(vocab_parts) if vocab_parts else "none used yet"

    # 3. Format prompt
    user_prompt = prompts.format_user_turn(
        user_text=user_text,
        vocab_words=daily_word_names,
        vocab_status=vocab_status,
    )
    
    # 4. Get context (excluding the last one we just added because we pass it as user_message)
    context = memory.get_context_with_vocab()
    
    try:
        response_text = llm.generate(
            user_message=user_prompt,
            context=context[:-1],
            system_prompt=prompts.SYSTEM_TUTOR + "\nIMPORTANT: You are ONLY the Tutor. Do not write the student's part. Respond with only your next sentence(s) in the conversation."
        )
            
        memory.add_turn("assistant", response_text)
        
        return {
            "response": response_text,
            "status": state_machine.state.name
        }
    except Exception as e:
        # Prevent app crash by providing a fallback message if LLM fails (e.g. no API key)
        error_msg = f"[System] The AI Coach is currently unavailable: {str(e)}"
        memory.add_turn("assistant", error_msg)
        return {
            "response": error_msg,
            "status": state_machine.state.name
        }
        

@app.get("/api/history")
def get_current_history(username: str = Query(...), session_id: str = Query(...)):
    """Gets the ongoing chat history for a specific user."""
    _, memory = get_user_systems(username, session_id)
    history = []
    for turn in memory._turns:
        history.append({
            "role": turn.role,
            "content": turn.content,
            "timestamp": turn.timestamp
        })
    return {"history": history}


@app.get("/api/profile")
def get_profile(username: str = Query(...)):
    """Real profile data from DB including historical progress"""
    vocab_system, memory = get_user_systems(username, "profile_view")
    
    import sqlite3
    db_path = str(config.get_db_path(username))
    
    avg_band = 0.0
    tests = 0
    words_mastered = 0
    history = []
    total_games = 0
    total_speaking_mins = 0
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 1. Overall Stats
        c.execute("SELECT AVG(estimated_band_score), COUNT(*), SUM(games_played), SUM(total_speaking_time_sec) FROM daily_progress WHERE estimated_band_score IS NOT NULL")
        row = c.fetchone()
        if row:
            avg_band = round(row[0], 1) if row[0] else 0.0
            tests = row[1] if row[1] else 0
            total_games = row[2] if row[2] else 0
            total_speaking_mins = round((row[3] / 60.0), 1) if row[3] else 0.0
            
        # 2. Vocabulary Mastered
        c.execute("SELECT COUNT(*) FROM vocabulary_progress WHERE is_mastered = 1")
        row2 = c.fetchone()
        if row2:
            words_mastered = row2[0]
            
        # 3. Last 7 Days History
        c.execute("SELECT date, estimated_band_score, total_turns FROM daily_progress ORDER BY date DESC LIMIT 7")
        rows = c.fetchall()
        for r in reversed(rows):
            history.append({
                "date": r[0],
                "band": r[1] if r[1] else 0.0,
                "turns": r[2] if r[2] else 0
            })
            
        conn.close()
    except Exception as e:
        print(f"Error fetching profile stats: {e}")
        pass
        
    return {
        "tests": tests,
        "avgBand": avg_band,
        "wordsMastered": words_mastered,
        "totalGames": total_games,
        "totalSpeakingMins": total_speaking_mins,
        "history": history
    }

@app.get("/api/games/{game_id}/new")
def get_new_game_round(game_id: str, username: str = Query(...), session_id: str = Query(...)):
    """Starts a new round for the specified game."""
    vocab_system, _ = get_user_systems(username, session_id)
    words = vocab_system.get_daily_words()
    
    if session_id not in ACTIVE_GAMES:
        ACTIVE_GAMES[session_id] = {}
        
    session_games = ACTIVE_GAMES[session_id]
    
    if game_id == "word_matching":
        game = WordMatchingGame(words)
        session_games["word_matching"] = game
        return {"questions": game.new_round(count=min(5, len(words)))}
        
    elif game_id == "sentence_completion":
        game = SentenceCompletionGame(words)
        session_games["sentence_completion"] = game
        return {"questions": game.new_round(count=min(5, len(words)))}
        
    elif game_id == "typing_speed":
        game = TypingSpeedGame()
        session_games["typing_speed"] = game
        return {"sentence": game.new_round()}
        
    elif game_id == "error_correction":
        game = ErrorCorrectionGame()
        session_games["error_correction"] = game
        return {"questions": game.new_round(count=4)}
        
    raise HTTPException(status_code=404, detail="Game not found")


@app.post("/api/games/{game_id}/check")
def check_game_answers(game_id: str, payload: dict, username: str = Query(...), session_id: str = Query(...)):
    """Checks the answers for the specified game."""
    _, memory = get_user_systems(username, session_id)
    
    if session_id not in ACTIVE_GAMES or game_id not in ACTIVE_GAMES[session_id]:
        raise HTTPException(status_code=400, detail="Game session not started or expired")
        
    game = ACTIVE_GAMES[session_id][game_id]
    
    try:
        if game_id == "word_matching":
            result = game.check_answers(payload.get("answers", {}))
        elif game_id == "sentence_completion":
            result = game.check_answers(payload.get("answers", []))
        elif game_id == "typing_speed":
            result = game.check_answer(payload.get("answer", ""))
        elif game_id == "error_correction":
            result = game.check_answers(payload.get("answers", []))
        else:
            raise HTTPException(status_code=404, detail="Game not found")
            
        # Update user stats
        memory.update_daily_progress(games_played=1, add_turn=False)
        
        return {
            "score": result.score,
            "total": result.total,
            "percentage": result.percentage,
            "time_seconds": result.time_seconds,
            "details": result.details
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/games")
def get_games():
    """Mock games endpoint for now"""
    return {
        "games": [
            {"id": "word_matching", "title": "Word Matching", "icon": "🔤", "desc": "Match words to their meanings"},
            {"id": "sentence_completion", "title": "Sentence Completion", "icon": "📝", "desc": "Fill in the blanks"},
            {"id": "typing_speed", "title": "Typing Speed", "icon": "⌨️", "desc": "Type sentences quickly"},
            {"id": "error_correction", "title": "Error Correction", "icon": "🔍", "desc": "Fix grammatical errors"}
        ]
    }

@app.get("/api/practice/{module}")
def get_practice_module(module: str):
    """Gets the content for a specific practice module."""
    if module == "speaking":
        return IELTSGuidance.get_speaking_topics()
    elif module == "reading":
        return IELTSGuidance.get_reading_practice_content()
    elif module == "listening":
        return IELTSGuidance.get_listening_practice_content()
    else:
        raise HTTPException(status_code=404, detail="Module not found")


@app.post("/api/practice/evaluate/{module}")
def evaluate_practice(module: str, payload: dict, username: str = Query(...), session_id: str = Query(...)):
    """Evaluate answers for a practice module."""
    vocab_system, memory = get_user_systems(username, session_id)
    
    if module in ["reading", "listening"]:
        user_answers = payload.get("answers", {})
        # Get actual content to compare answers
        if module == "reading":
            content = IELTSGuidance.get_reading_practice_content()
        else:
            content = IELTSGuidance.get_listening_practice_content()
            
        questions = content.get("questions", [])
        correct_count = 0
        total_questions = len(questions)
        
        for q in questions:
            q_id = q["id"]
            correct_ans = q["answer"]
            if user_answers.get(q_id) == correct_ans:
                correct_count += 1
        
        # Simple band score mapping: 4/4=9, 3/4=7.5, 2/4=6, 1/4=4.5, 0=0
        if total_questions > 0:
            percentage = correct_count / total_questions
            if percentage >= 1.0: band = 9.0
            elif percentage >= 0.75: band = 7.5
            elif percentage >= 0.5: band = 6.0
            elif percentage >= 0.25: band = 4.5
            else: band = 0.0
        else:
            band = 0.0
            
        # Record progress
        memory.update_daily_progress(band_score=band, add_turn=False)
        
        return {
            "status": "success", 
            "correct_count": correct_count, 
            "total": total_questions,
            "estimated_band": band
        }
        
    elif module == "speaking":
        text = payload.get("text", "")
        duration = payload.get("duration_seconds", 0)
        topic = payload.get("topic", "")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required for speaking evaluation")
            
        try:
            scorer = IELTSScorer()
            scorer.set_llm(get_llm())
            
            if duration <= 0:
                word_count = len(text.split())
                duration = (word_count / 130.0) * 60.0
                
            result = scorer.evaluate(text, duration, topic)
            
            if result and result.get("overall_band", 0) > 0:
                memory.update_daily_progress(speaking_time_sec=duration, band_score=result["overall_band"], add_turn=False)
                return result
            else:
                raise HTTPException(status_code=400, detail="Evaluation failed to produce a valid score")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Scoring error: {str(e)}")
            
@app.post("/api/practice/evaluate_audio/speaking")
async def evaluate_speaking_audio(
    file: UploadFile = File(...),
    username: str = Form(...),
    session_id: str = Form(...),
    topic: str = Form(...),
    duration_seconds: float = Form(...)
):
    """Evaluate speaking practice from an uploaded audio file using Whisper STT."""
    try:
        from faster_whisper import WhisperModel
        import config
    except ImportError:
        raise HTTPException(status_code=500, detail="STT dependencies not available on server")

    _, memory = get_user_systems(username, session_id)
    
    # Save the uploaded file temporarily
    fd, temp_path = tempfile.mkstemp(suffix=".m4a")
    try:
        with os.fdopen(fd, 'wb') as temp_file:
            content = await file.read()
            temp_file.write(content)
            
        # Transcribe audio
        model = WhisperModel(config.WHISPER_MODEL_SIZE, device=config.WHISPER_DEVICE, compute_type=config.WHISPER_COMPUTE_TYPE)
        segments, info = model.transcribe(temp_path, beam_size=config.WHISPER_BEAM_SIZE, language=config.WHISPER_LANGUAGE)
        
        transcribed_text = " ".join([segment.text for segment in segments]).strip()
        
        if not transcribed_text:
            raise HTTPException(status_code=400, detail="Could not detect any speech in the audio.")
            
        # Perform Evaluation logic matching the text-based endpoint
        scorer = IELTSScorer()
        scorer.set_llm(get_llm())
        
        if duration_seconds <= 0:
            word_count = len(transcribed_text.split())
            duration_seconds = (word_count / 130.0) * 60.0
            
        result = scorer.evaluate(transcribed_text, duration_seconds, topic)
        
        if result and result.get("overall_band", 0) > 0:
            memory.update_daily_progress(speaking_time_sec=duration_seconds, band_score=result["overall_band"], add_turn=False)
            
            # Augment result with transcribed text to display on frontend
            result["transcribed_text"] = transcribed_text
            return result
        else:
            raise HTTPException(status_code=400, detail="Evaluation failed to produce a valid score")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio evaluation error: {str(e)}")
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/api/practice/{module}")
def get_practice_module(module: str):
    """Gets the content for a specific practice module."""
    if module == "speaking":
        return IELTSGuidance.get_speaking_topics()
    elif module == "reading":
        return IELTSGuidance.get_reading_practice_content()
    elif module == "listening":
        return IELTSGuidance.get_listening_practice_content()
    else:
        raise HTTPException(status_code=404, detail="Module not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
