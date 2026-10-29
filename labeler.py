import requests
import streamlit as st

# ---- Settings ----------------------------------------------------------
BUSINESS = "an independent bookstore"
LABELS = [
    "book_availability",
    "staff_service",
    "store_atmosphere",
    "pricing_value",
    "events_community",
    "other",
]
GUIDE = """Choose exactly one label from this list:
- book_availability: Whether the store has the books or genres customers want, including stock, selection, and special orders.
- staff_service: Helpfulness, knowledge, friendliness, or responsiveness of staff.
- store_atmosphere: Store layout, comfort, cleanliness, noise, and how enjoyable it is to browse.
- pricing_value: Prices, discounts, loyalty offers, and perceived value for money.
- events_community: Author talks, book clubs, children's activities, and community events.
- other: Feedback that does not fit the categories above or is too vague to classify.
Return only the exact label text, in lowercase, with no explanation.
If a comment mentions multiple topics, choose the main issue or the topic most emphasized.
Do not infer a topic that the customer did not mention."""
MODEL = "openai/gpt-oss-20b"
URL = "https://api.groq.com/openai/v1/chat/completions"
# ------------------------------------------------------------------------


def label_comment(text):
    """Return one category label, or 'unclear' if the response is invalid."""
    key = st.secrets["GROQ_API_KEY"]
    prompt = f"You label customer comments for {BUSINESS}.\n{GUIDE}\n\nComment: {text}"
    response = requests.post(
        URL,
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": MODEL,
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    response.raise_for_status()
    answer = response.json()["choices"][0]["message"]["content"]
    label = answer.strip().lower().replace(" ", "_")
    return label if label in LABELS else "unclear"
