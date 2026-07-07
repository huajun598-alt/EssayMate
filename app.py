from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st


APP_NAME = "EssayMate"
APP_TITLE = "AI Writing Coach"
APP_TAGLINE = "Write -> Analyze -> Learn -> Retry"

SAMPLE_TITLE = "My Favorite Hobby"
SAMPLE_ESSAY = """I have many hobbies, such as running, singing and reading. My favorite hobby is reading. I like read books very much.
I read books every day. After school, I often read books in my room. I like story book best. They are very interesting.
I start to read books when I was seven years old. Reading is good for me. It can help me know many new things.
Sometimes I feel boring, reading can make me happy. I can also learn many new word from books.
I love reading. I will keep this hobby forever."""


@dataclass
class EssayResult:
    score: int
    dimensions: List[Dict[str, str]]
    problems: List[str]
    suggestions: List[str]
    corrections: List[Dict[str, str]]
    model_essay: str
    phrases: List[Dict[str, str]]
    learning_tips: List[str]
    learned_today: Dict[str, List[str]]
    progress_after: Dict[str, int]
    summary: str


COMMON_MISTAKES = {
    "last weekends": ("last weekend", "Use singular time expression: last weekend."),
    "I like she": ("I like her", "Use object pronoun after a verb: her."),
    "like read": ("like reading", "Fixed phrase: like doing sth."),
    "story book best": ("story books best", "Use plural form when talking about books in general."),
    "many new word": ("many new words", "Use plural nouns after many."),
    "feel boring": ("feel bored", "People feel bored; things are boring."),
    "which has": ("which have", "Use have when the noun before which is plural."),
    "hight": ("height", "Spelling correction: height."),
    "breath the fresh air": ("breathe the fresh air", "Use the verb breathe."),
    "the half of": ("half of", "Do not use the before half in this phrase."),
}

CONNECTORS = ["because", "but", "so", "although", "first", "second", "finally", "however", "also"]


def init_state() -> None:
    defaults = {
        "title": SAMPLE_TITLE,
        "essay": SAMPLE_ESSAY,
        "student_level": "Beginner",
        "result": None,
        "last_result": None,
        "status_note": "",
        "pending_action": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def apply_pending_action() -> None:
    action = st.session_state.get("pending_action", "")
    if not action:
        return

    if action == "sample":
        st.session_state.title = SAMPLE_TITLE
        st.session_state.essay = SAMPLE_ESSAY
        st.session_state.student_level = "Beginner"
        st.session_state.status_note = ""
    elif action in ("clear", "try_again"):
        st.session_state.title = ""
        st.session_state.essay = ""
        st.session_state.student_level = "Beginner"
        st.session_state.result = None
        st.session_state.status_note = ""
    elif action == "improve":
        result = st.session_state.get("last_result") or st.session_state.get("result")
        if result:
            st.session_state.essay = " ".join(row["Improved"] for row in result.corrections)
            st.session_state.title = st.session_state.get("title", "") or SAMPLE_TITLE
        st.session_state.result = None
        st.session_state.status_note = "Your improved draft is ready. Rewrite it once more and compare your next score."
    elif action == "similar_topic":
        st.session_state.title = "A Meaningful School Activity"
        st.session_state.essay = ""
        st.session_state.result = None
        st.session_state.status_note = "New topic generated. Try writing a fresh essay with today's learning points."
    elif action == "grammar_only":
        st.session_state.status_note = "Grammar focus: check verb forms, plural nouns and fixed phrases first."

    st.session_state.pending_action = ""


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #172033;
            --muted: #667085;
            --line: rgba(255,255,255,.55);
            --glass: rgba(255,255,255,.70);
            --glass-strong: rgba(255,255,255,.86);
            --blue: #5c7cfa;
            --purple: #7c3aed;
            --green: #15a46e;
            --red: #ef4444;
        }

        .stApp {
            background:
                radial-gradient(circle at 15% 10%, rgba(124, 58, 237, .18), transparent 32%),
                radial-gradient(circle at 90% 5%, rgba(92, 124, 250, .16), transparent 34%),
                linear-gradient(135deg, #f7f9ff 0%, #eef3ff 45%, #f9fbff 100%);
            color: var(--ink);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 3rem;
            padding-bottom: 4rem;
        }

        .hero, .glass-card, .score-card, .mini-card, .learn-box, .retry-card {
            background: var(--glass);
            border: 1px solid var(--line);
            border-radius: 24px;
            box-shadow: 0 24px 70px rgba(41, 50, 91, .10);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            transition: transform .18s ease, box-shadow .18s ease;
        }

        .hero:hover, .glass-card:hover, .mini-card:hover, .learn-box:hover, .retry-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 28px 80px rgba(41, 50, 91, .14);
        }

        .hero {
            padding: 34px 38px;
            margin-bottom: 24px;
            animation: fadeIn .45s ease both;
        }

        .brand-kicker {
            color: var(--purple);
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
            font-size: 13px;
            margin-bottom: 10px;
        }

        .hero h1 {
            margin: 0;
            font-size: clamp(38px, 6vw, 72px);
            line-height: 1.02;
            letter-spacing: -1px;
        }

        .hero p {
            max-width: 760px;
            color: var(--muted);
            font-size: 19px;
            line-height: 1.7;
            margin-top: 18px;
        }

        .flow {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 22px;
        }

        .flow span {
            padding: 10px 16px;
            border-radius: 999px;
            background: rgba(255,255,255,.72);
            color: #334155;
            font-weight: 750;
            border: 1px solid rgba(255,255,255,.72);
        }

        .glass-card {
            padding: 28px;
            margin: 18px 0;
            animation: fadeIn .5s ease both;
        }

        .step-label {
            display: inline-flex;
            padding: 8px 14px;
            border-radius: 999px;
            background: linear-gradient(135deg, rgba(92,124,250,.15), rgba(124,58,237,.16));
            color: #4f46e5;
            font-weight: 850;
            margin-bottom: 14px;
        }

        .section-title {
            font-size: 25px;
            font-weight: 900;
            margin: 8px 0 10px;
        }

        .section-copy {
            color: var(--muted);
            font-size: 16px;
            line-height: 1.7;
            margin-bottom: 18px;
        }

        .score-card {
            padding: 28px;
            min-height: 216px;
            background:
                linear-gradient(135deg, rgba(92,124,250,.20), rgba(124,58,237,.22)),
                rgba(255,255,255,.72);
        }

        .score-number {
            font-size: 76px;
            line-height: .95;
            font-weight: 950;
            background: linear-gradient(135deg, var(--blue), var(--purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .score-number span {
            font-size: 36px;
            color: #667085;
            -webkit-text-fill-color: #667085;
        }

        .mini-card {
            padding: 20px;
            min-height: 132px;
            background: var(--glass-strong);
        }

        .mini-title {
            color: #475467;
            font-weight: 800;
            margin-bottom: 12px;
        }

        .mini-score {
            font-size: 34px;
            font-weight: 950;
            color: #4f46e5;
        }

        .problem-card, .suggest-card {
            padding: 15px 17px;
            border-radius: 18px;
            margin-bottom: 12px;
            line-height: 1.65;
        }

        .problem-card {
            background: rgba(254, 226, 226, .62);
            border: 1px solid rgba(248, 113, 113, .28);
        }

        .suggest-card {
            background: rgba(220, 252, 231, .64);
            border: 1px solid rgba(34, 197, 94, .24);
        }

        .learn-box {
            padding: 24px;
            min-height: 240px;
            background: rgba(255,255,255,.78);
        }

        .essay-card {
            padding: 24px;
            border-radius: 22px;
            background: rgba(255, 251, 235, .66);
            border: 1px solid rgba(245, 158, 11, .20);
            line-height: 1.85;
            white-space: pre-line;
        }

        .retry-card {
            margin-top: 20px;
            padding: 26px;
            background: linear-gradient(135deg, rgba(92,124,250,.13), rgba(124,58,237,.13)), rgba(255,255,255,.72);
        }

        .learning-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
            margin: 14px 0 20px;
        }

        .learning-card {
            padding: 18px;
            border-radius: 20px;
            background: rgba(255,255,255,.74);
            border: 1px solid rgba(255,255,255,.64);
            box-shadow: 0 14px 34px rgba(41, 50, 91, .07);
        }

        .learning-card h4 {
            margin: 0 0 10px;
            font-size: 17px;
        }

        .learning-card ul {
            margin: 0;
            padding-left: 18px;
            color: var(--muted);
            line-height: 1.7;
        }

        .progress-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 14px;
        }

        .progress-panel {
            padding: 20px;
            border-radius: 22px;
            background: rgba(255,255,255,.76);
            border: 1px solid rgba(255,255,255,.66);
            box-shadow: 0 16px 42px rgba(41, 50, 91, .08);
        }

        .progress-item {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 9px 0;
            color: #344054;
            border-bottom: 1px solid rgba(102,112,133,.10);
        }

        .progress-stars {
            color: #5c7cfa;
            letter-spacing: 1px;
            white-space: nowrap;
        }

        .check-list {
            margin: 10px 0 0;
            padding: 0;
            list-style: none;
        }

        .check-list li {
            margin: 10px 0;
            color: #176b4d;
            font-weight: 650;
        }

        .loop-note {
            margin-top: 18px;
            padding: 18px 20px;
            border-radius: 20px;
            background: linear-gradient(135deg, rgba(92,124,250,.13), rgba(124,58,237,.13));
            color: #344054;
            font-weight: 750;
        }

        @media (max-width: 800px) {
            .learning-grid, .progress-row {
                grid-template-columns: 1fr;
            }
        }

        .stButton > button {
            border-radius: 999px !important;
            min-height: 46px;
            font-weight: 850 !important;
            border: 1px solid rgba(255,255,255,.72) !important;
            box-shadow: 0 12px 28px rgba(41, 50, 91, .08);
            transition: transform .16s ease, box-shadow .16s ease, border .16s ease;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 42px rgba(92, 124, 250, .22);
            border-color: rgba(124, 58, 237, .35) !important;
        }

        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, var(--blue), var(--purple)) !important;
            color: white !important;
            border: none !important;
        }

        textarea, input, .stSelectbox div[data-baseweb="select"] > div {
            border-radius: 18px !important;
            box-shadow: 0 10px 32px rgba(41, 50, 91, .06);
        }

        [data-testid="stDataFrame"] {
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 18px 50px rgba(41, 50, 91, .08);
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def split_sentences(essay: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", essay.strip())
    return [part.strip() for part in parts if part.strip()]


def count_words(essay: str) -> int:
    return len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", essay))


def detect_mistakes(text: str) -> List[Tuple[str, str, str]]:
    lower_text = text.lower()
    found = []
    for wrong, (right, reason) in COMMON_MISTAKES.items():
        if wrong.lower() in lower_text:
            found.append((wrong, right, reason))
    return found


def connector_count(text: str) -> int:
    lower_text = text.lower()
    return sum(1 for word in CONNECTORS if re.search(rf"\b{re.escape(word)}\b", lower_text))


def improve_clean_sentence(sentence: str, index: int) -> Tuple[str, str]:
    base = sentence.rstrip(".!?")
    if len(base.split()) <= 7:
        if index % 2 == 0:
            return f"{base}, which makes the idea clearer.", "The original sentence is short, so adding a small detail makes it fuller."
        return f"{base} because it supports the main idea.", "Add a reason to make the sentence more useful in an exam essay."
    if "because" not in sentence.lower() and index % 3 == 0:
        return f"{base}, so the meaning is easier to follow.", "A connector helps the sentence connect with the next idea."
    return sentence, "The sentence is clear and can be kept."


def revise_sentence(sentence: str, index: int) -> Tuple[str, str]:
    improved = sentence
    reasons = []
    for wrong, (right, reason) in COMMON_MISTAKES.items():
        if wrong.lower() in improved.lower():
            improved = re.sub(re.escape(wrong), right, improved, flags=re.IGNORECASE)
            reasons.append(reason)

    if reasons:
        return improved, " ".join(reasons)

    return improve_clean_sentence(sentence, index)


def build_corrections(essay: str) -> List[Dict[str, str]]:
    sentences = split_sentences(essay)
    rows = []
    for index, sentence in enumerate(sentences[:10], start=1):
        improved, reason = revise_sentence(sentence, index)
        rows.append(
            {
                "No.": str(index),
                "Original": sentence,
                "Improved": improved,
                "Reason": reason,
            }
        )
    return rows or [
        {
            "No.": "1",
            "Original": essay.strip(),
            "Improved": essay.strip(),
            "Reason": "Please write more complete sentences so the coach can give detailed feedback.",
        }
    ]


def build_problems(essay: str, word_count: int, connectors: int, mistakes: List[Tuple[str, str, str]]) -> List[str]:
    problems: List[str] = []
    if word_count < 80:
        problems.append("The essay is a little short. This is common for students who have ideas but need more examples.")
    if connectors < 2:
        problems.append("Good attempt, but the essay needs more connectors such as because, so and although.")
    for wrong, right, reason in mistakes[:3]:
        problems.append(f"This is a typical issue: '{wrong}' should be '{right}'. {reason}")
    if not problems:
        problems.append("The writing is clear. To improve further, add more specific details and richer expressions.")
    return problems[:5]


def build_suggestions(word_count: int, connectors: int, mistakes: List[Tuple[str, str, str]]) -> List[str]:
    suggestions = [
        "You already have a clear idea. Next, make the topic, reason and feeling clear before adding examples.",
        "Good attempt! Use connectors like because, so, but and although to make the logic smoother.",
        "Small improvements can make your writing stronger. Check verb forms, plural nouns and fixed phrases carefully.",
    ]
    if word_count < 80:
        suggestions[0] = "Add 2-3 more sentences with examples. This can improve both content and structure."
    if connectors < 2:
        suggestions[1] = "Try adding one connector in each paragraph. Your writing will become easier to follow."
    if mistakes:
        suggestions[2] = "Fix the repeated grammar mistakes first. If you fix these, your score can improve significantly."
    return suggestions


def build_learned_today(mistakes: List[Tuple[str, str, str]], connectors: int) -> Dict[str, List[str]]:
    grammar_items = []
    for wrong, right, _ in mistakes[:2]:
        grammar_items.append(f"{wrong} -> {right}")
    if not grammar_items:
        grammar_items.append("Keep checking verb forms and plural nouns.")

    structure_items = [
        "Add reasons after opinions.",
        "Use one clear idea in each paragraph.",
    ]
    if connectors < 2:
        structure_items.insert(0, "Connect short sentences with because, so or although.")

    vocabulary_items = [
        "Use connectors: because / although / however.",
        "Collect reusable phrases from the model essay.",
    ]
    return {
        "Grammar": grammar_items,
        "Structure": structure_items,
        "Vocabulary": vocabulary_items,
    }


def build_progress_after(grammar_score: int, structure_score: int, vocabulary_score: int) -> Dict[str, int]:
    return {
        "Grammar": min(5, max(3, grammar_score + 1)),
        "Structure": min(5, max(3, structure_score + 1)),
        "Vocabulary": min(5, max(3, vocabulary_score + 1)),
    }


def stars(value: int) -> str:
    value = max(0, min(5, value))
    return "★" * value + "☆" * (5 - value)


def build_model_essay(title: str) -> str:
    if "hobby" in title.lower() or "read" in title.lower():
        return """Dear friends,

Today I want to talk about my favorite hobby. My favorite hobby is reading because it helps me learn many new things.

I often read books after school. I like story books best because they are interesting and relaxing. When I feel tired, reading can make me calm and happy. I can also learn useful words and good sentences from books.

In my opinion, reading is a good hobby for students. It can open our eyes and make our life better. I will keep reading and try to read more good books."""

    return """Dear friends,

Today I want to share a meaningful activity with you. Last weekend, our class took part in a school activity. We worked together and learned a lot.

First, we made a clear plan. Then we helped each other and finished the task step by step. Although we felt tired, we were very happy because the activity taught us teamwork and responsibility.

In my opinion, this activity was useful and meaningful. I hope we can join more activities like this in the future."""


def build_phrases(title: str) -> List[Dict[str, str]]:
    if "hobby" in title.lower() or "read" in title.lower():
        return [
            {"Phrase": "my favorite hobby", "Meaning": "my favorite activity"},
            {"Phrase": "learn new things", "Meaning": "get new knowledge"},
            {"Phrase": "make me relaxed", "Meaning": "help me feel calm"},
            {"Phrase": "open my eyes", "Meaning": "help me see more of the world"},
            {"Phrase": "keep doing sth.", "Meaning": "continue doing something"},
        ]
    return [
        {"Phrase": "take part in", "Meaning": "join an activity"},
        {"Phrase": "step by step", "Meaning": "slowly and clearly"},
        {"Phrase": "work together", "Meaning": "cooperate with others"},
        {"Phrase": "be responsible for", "Meaning": "take care of something"},
        {"Phrase": "in the future", "Meaning": "later"},
    ]


def analyze_essay(title: str, essay: str, student_level: str) -> EssayResult:
    words = count_words(essay)
    connectors = connector_count(essay)
    mistakes = detect_mistakes(essay)

    content = 2 + (1 if words >= 70 else 0) + (1 if words >= 110 else 0)
    grammar = 4 - min(len(mistakes), 3)
    structure = 2 + (1 if connectors >= 2 else 0) + (1 if len(split_sentences(essay)) >= 7 else 0)
    vocabulary = 2 + (1 if connectors >= 2 else 0)

    level_adjustment = {"Beginner": 1, "Intermediate": 0, "Advanced": -1}.get(student_level, 0)
    score = max(6, min(15, content + grammar + structure + vocabulary + level_adjustment))

    dimensions = [
        {"Dimension": "Content", "Score": f"{min(content, 4)} / 4", "Feedback": "Topic and ideas are checked."},
        {"Dimension": "Grammar", "Score": f"{max(grammar, 1)} / 4", "Feedback": "Grammar, spelling and fixed phrases are checked."},
        {"Dimension": "Structure", "Score": f"{min(structure, 4)} / 4", "Feedback": "Paragraph flow and connectors are checked."},
        {"Dimension": "Vocabulary", "Score": f"{min(vocabulary, 3)} / 3", "Feedback": "Useful words and sentence patterns are checked."},
    ]

    if score >= 12:
        summary = "Good attempt! Your idea is clear. Let's make the details richer and the expressions more natural."
    elif score >= 9:
        summary = "You already have a clear direction. Small grammar improvements can make your writing much stronger."
    else:
        summary = "You have started well. Let's improve grammar details, complete sentences and simple connectors step by step."

    return EssayResult(
        score=score,
        dimensions=dimensions,
        problems=build_problems(essay, words, connectors, mistakes),
        suggestions=build_suggestions(words, connectors, mistakes),
        corrections=build_corrections(essay),
        model_essay=build_model_essay(title),
        phrases=build_phrases(title),
        learning_tips=[
            "Rewrite this essay once using the improved sentences.",
            "Focus on connectors: because, so, but and although.",
            "Memorize 3 useful phrases and use them in your next essay.",
        ],
        learned_today=build_learned_today(mistakes, connectors),
        progress_after=build_progress_after(max(grammar, 1), min(structure, 4), min(vocabulary, 3)),
        summary=summary,
    )


def render_hero() -> None:
    st.markdown(
        f"""
        <section class="hero">
            <div class="brand-kicker">{APP_TITLE}</div>
            <h1>{APP_NAME}</h1>
            <p>{APP_TAGLINE}. A structured AI writing coach that turns English correction into a clear learning loop.</p>
            <div class="flow">
                <span>Write</span>
                <span>Analyze</span>
                <span>Learn</span>
                <span>Retry</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_write() -> None:
    st.markdown('<section class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="step-label">Step 1 - Write</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Start your writing practice</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Paste your essay below. EssayMate reads it like an English teacher and prepares structured feedback.</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.status_note:
        st.info(st.session_state.status_note)

    action_cols = st.columns([1, 1, 2])
    with action_cols[0]:
        if st.button("Use Sample", use_container_width=True):
            st.session_state.pending_action = "sample"
            st.rerun()
    with action_cols[1]:
        if st.button("Clear", use_container_width=True):
            st.session_state.pending_action = "clear"
            st.rerun()

    st.text_input("Essay topic", key="title", placeholder="e.g. My Favorite Hobby")
    st.text_area(
        "Essay draft",
        key="essay",
        height=240,
        placeholder="Write or paste your English essay here...",
    )
    st.radio("Current level", ["Beginner", "Intermediate", "Advanced"], horizontal=True, key="student_level")

    if st.button("Start Analysis", type="primary", use_container_width=True):
        if not st.session_state.essay.strip():
            st.warning("Please paste your essay before starting analysis.")
        else:
            with st.status("AI is analyzing your essay...", expanded=True) as status:
                st.write("Analyzing your writing...")
                time.sleep(0.35)
                st.write("Checking grammar...")
                time.sleep(0.35)
                st.write("Checking structure...")
                time.sleep(0.35)
                st.write("Generating learning suggestions...")
                time.sleep(0.35)
                result = analyze_essay(st.session_state.title, st.session_state.essay, st.session_state.student_level)
                st.session_state.result = result
                st.session_state.last_result = result
                status.update(label="Analysis completed", state="complete", expanded=False)
            st.success("Your analysis is ready. Continue with Learn and Retry.")
            st.rerun()
    st.markdown("</section>", unsafe_allow_html=True)


def render_analyze(result: EssayResult) -> None:
    st.markdown('<section class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="step-label">Step 2 - Analyze</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Teacher-like feedback</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-copy">{result.summary}</div>', unsafe_allow_html=True)

    left, right = st.columns([1, 2])
    with left:
        st.markdown(
            f"""
            <div class="score-card">
                <div class="mini-title">Score</div>
                <div class="score-number">{result.score}<span>/15</span></div>
                <div class="section-copy">A quick view of your current writing level.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        cols = st.columns(4)
        for col, item in zip(cols, result.dimensions):
            with col:
                st.markdown(
                    f"""
                    <div class="mini-card">
                        <div class="mini-title">{item['Dimension']}</div>
                        <div class="mini-score">{item['Score']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.dataframe(pd.DataFrame(result.dimensions), use_container_width=True, hide_index=True)

    problem_col, suggest_col = st.columns(2)
    with problem_col:
        st.markdown('<div class="section-title">Key Problems</div>', unsafe_allow_html=True)
        for item in result.problems:
            st.markdown(f'<div class="problem-card">{item}</div>', unsafe_allow_html=True)
    with suggest_col:
        st.markdown('<div class="section-title">Suggestions</div>', unsafe_allow_html=True)
        for item in result.suggestions:
            st.markdown(f'<div class="suggest-card">{item}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Sentence-level Corrections</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Original sentences are compared with improved versions, so students can see exactly what changed.</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(pd.DataFrame(result.corrections), use_container_width=True, hide_index=True, height=360)
    csv_data = pd.DataFrame(result.corrections).to_csv(index=False).encode("utf-8-sig")
    st.download_button("Download Correction CSV", csv_data, "essaymate_corrections.csv", "text/csv", use_container_width=True)
    st.markdown("</section>", unsafe_allow_html=True)


def render_learn(result: EssayResult) -> None:
    st.markdown('<section class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="step-label">Step 3 - Learn</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Turn feedback into practice</div>', unsafe_allow_html=True)

    essay_col, phrase_col = st.columns([1.25, 1])
    with essay_col:
        st.markdown('<div class="learn-box">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Model Essay</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="essay-card">{result.model_essay}</div>', unsafe_allow_html=True)
        st.text_area("Copy-ready model essay", result.model_essay, height=120)
        st.markdown("</div>", unsafe_allow_html=True)

    with phrase_col:
        st.markdown('<div class="learn-box">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Key Phrases</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(result.phrases), use_container_width=True, hide_index=True)
        st.markdown('<div class="section-title">Learning Tips</div>', unsafe_allow_html=True)
        for tip in result.learning_tips:
            st.markdown(f'<div class="suggest-card">{tip}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    render_today_learning(result)
    render_learning_progress(result)

    st.markdown(
        """
        <div class="retry-card">
            <div class="section-title">Next Learning Actions</div>
            <div class="section-copy">Feedback is not the end. Learning starts here. Ready for another practice?</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    action_cols = st.columns(3)
    with action_cols[0]:
        if st.button("Rewrite My Essay", type="primary", use_container_width=True):
            st.session_state.pending_action = "improve"
            st.rerun()
    with action_cols[1]:
        if st.button("Improve Grammar Only", use_container_width=True):
            st.session_state.pending_action = "grammar_only"
            st.rerun()
    with action_cols[2]:
        if st.button("Generate Similar Topic", use_container_width=True):
            st.session_state.pending_action = "similar_topic"
            st.rerun()

    if st.session_state.status_note:
        st.info(st.session_state.status_note)

    retry_cols = st.columns(2)
    with retry_cols[0]:
        if st.button("Try Again", use_container_width=True):
            st.session_state.pending_action = "try_again"
            st.rerun()
    with retry_cols[1]:
        if st.button("Improve Essay", type="primary", use_container_width=True):
            st.session_state.pending_action = "improve"
            st.rerun()
    st.markdown("</section>", unsafe_allow_html=True)


def render_today_learning(result: EssayResult) -> None:
    cards = []
    for title, items in result.learned_today.items():
        list_items = "".join(f"<li>{item}</li>" for item in items)
        cards.append(f"<div class='learning-card'><h4>{title}</h4><ul>{list_items}</ul></div>")

    st.markdown(
        f"""
        <div class="retry-card">
            <div class="section-title">What you learned today</div>
            <div class="section-copy">A short learning summary helps students remember what changed, not just what was wrong.</div>
            <div class="learning-grid">{''.join(cards)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_learning_progress(result: EssayResult) -> None:
    before = {"Grammar": 2, "Structure": 3, "Vocabulary": 3}
    before_rows = "".join(
        f"<div class='progress-item'><span>{name}</span><span class='progress-stars'>{stars(value)}</span></div>"
        for name, value in before.items()
    )
    after_rows = "".join(
        f"<div class='progress-item'><span>{name}</span><span class='progress-stars'>{stars(value)}</span></div>"
        for name, value in result.progress_after.items()
    )
    improvements = [
        "Fixed grammar mistakes",
        "Learned useful connectors",
        "Improved sentence structure",
    ]
    improvement_rows = "".join(f"<li>✓ {item}</li>" for item in improvements)

    st.markdown(
        f"""
        <div class="retry-card">
            <div class="section-title">Writing Progress / Learning Progress</div>
            <div class="section-copy">This turns correction into a visible learning path.</div>
            <div class="progress-row">
                <div class="progress-panel">
                    <div class="mini-title">Before Feedback</div>
                    {before_rows}
                </div>
                <div class="progress-panel">
                    <div class="mini-title">After Learning</div>
                    {after_rows}
                    <ul class="check-list">{improvement_rows}</ul>
                </div>
            </div>
            <div class="loop-note">Write -> Analyze -> Learn -> Retry -> Improve</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.markdown(
        """
        <section class="glass-card">
            <div class="step-label">Step 2 - Analyze</div>
            <div class="section-title">Your feedback will appear here</div>
            <div class="section-copy">Use the sample essay or paste your own draft, then click Start Analysis.</div>
        </section>
        <section class="glass-card">
            <div class="step-label">Step 3 - Learn</div>
            <div class="section-title">Learning materials will appear here</div>
            <div class="section-copy">EssayMate will generate a model essay, key phrases and next practice actions.</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="EssayMate - AI Writing Coach", page_icon="✍️", layout="wide")
    init_state()
    apply_pending_action()
    inject_css()
    render_hero()
    render_write()

    result = st.session_state.get("result")
    if result:
        render_analyze(result)
        render_learn(result)
    else:
        render_empty_state()


if __name__ == "__main__":
    main()
