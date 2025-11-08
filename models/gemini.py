#!/usr/bin/env python3
"""
gemini_plan.py
===========================
・Stage1 の summary.txt を読み取り
・現在のポートフォリオ情報（state.json or デフォルト）を組み込み
・Gemini に「もし自分ならこう行動する」という自然文プランを生成させる
・結果を decision_plan.txt に保存

Requirements:
    pip install google-generativeai
Environment:
    export GEMINI_API_KEY=YOUR_KEY
"""

import os, json, datetime as dt
import google.generativeai as genai

# ====== CONFIG ======
MODEL          = "models/gemini-2.5-pro"
TEMP           = 0.3
MAX_TOKENS     = 5000
IN_SUMMARY     = "summary.txt"
OUT_PLAN       = "decision_plan.txt"
OPTIONAL_STATE = "state.json"

GEMINI_API_KEY = "AIzaSyAguY8tFf8snXyFHUsGFlE8BqMOdy1Nwr8"

# デフォルト口座情報
STATE_DEFAULT = {
    "ticker": "META",
    "current_price": 143.73,
    "cash": 1000.0,
    "position": {"side": "flat", "shares": 0, "avg_entry": None},
    "constraints": {
        "max_leverage": 1.0,
        "max_position_pct": 0.9,
        "risk_per_trade_pct": 0.5,
    },
    "costs": {"fee_bps": 2, "slip_bps": 1},
    "horizon_minutes": 60,
}
# =====================


def load_state():
    """state.json があれば読み込み、なければデフォルト"""
    if os.path.exists(OPTIONAL_STATE):
        try:
            with open(OPTIONAL_STATE, "r", encoding="utf-8") as f:
                user = json.load(f)

            def merge(a, b):
                out = dict(a)
                for k, v in b.items():
                    if isinstance(v, dict) and k in out and isinstance(out[k], dict):
                        out[k] = merge(out[k], v)
                    else:
                        out[k] = v
                return out

            return merge(STATE_DEFAULT, user)
        except Exception as e:
            print("⚠️ state.json 読み込み失敗:", e)
    return STATE_DEFAULT


def build_prompt(summary_text: str, state: dict) -> str:
    """Gemini への自然文プロンプト"""
    return f"""
You are an experienced discretionary trader mentoring a junior analyst.

Inputs:
- Recent context (summary of current conditions):
\"\"\"{summary_text.strip()[:7000]}\"\"\"
- Current portfolio state (JSON):
{json.dumps(state, ensure_ascii=False, indent=2)}

Task:
Speak **as yourself** (first-person).
Describe exactly what *you* would do next given these conditions.

Include:
1. What position (if any) you would take or change.
2. How you would size it (approx. % of capital or shares).
3. Your intended stop, target, and holding horizon.
4. How you would monitor and when you would reconsider or exit.
5. The reasoning behind your choices.

Rules:
- Respond in natural English paragraphs (not JSON).
- Use first-person voice: "I would...", "I plan to...", "My reasoning is...".
- Be specific, concise (~300–500 words).
- Avoid generic disclaimers or advisory language.
- Output **only the plan text**, nothing else.
""".strip()


def call_gemini(prompt: str) -> str:
    """Gemini から自然文プランを取得"""
    api_key = GEMINI_API_KEY
    if not api_key:
        raise SystemExit("❌ GEMINI_API_KEY not set. Use: export GEMINI_API_KEY=YOUR_KEY")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL)

    resp = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=TEMP,
            max_output_tokens=MAX_TOKENS,
            response_mime_type="text/plain",
        ),
        safety_settings=[
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        ],
    )

    if not getattr(resp, "candidates", None):
        return "No response."

    parts = getattr(getattr(resp.candidates[0], "content", None), "parts", []) or []
    text = "".join(getattr(p, "text", "") for p in parts).strip()
    return text or "No response."


def main():
    if not os.path.exists(IN_SUMMARY):
        raise SystemExit(f"❌ {IN_SUMMARY} not found. Run stage 1 first.")

    with open(IN_SUMMARY, "r", encoding="utf-8") as f:
        summary_text = f.read()

    state = load_state()
    prompt = build_prompt(summary_text, state)
    print("=== Sending prompt to Gemini ===")
    print(prompt[:400], "...\n")

    plan_text = call_gemini(prompt)

    with open(OUT_PLAN, "w", encoding="utf-8") as f:
        f.write(plan_text)

    print("=== PLAN OUTPUT ===")
    print(plan_text[:800])
    print(f"\n✅ Saved to {OUT_PLAN} ({dt.datetime.now().isoformat(timespec='seconds')})")


if __name__ == "__main__":
    main()
