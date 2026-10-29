import os

import pandas as pd
import plotly.express as px
import streamlit as st

from labeler import LABELS, label_comment

# ---- Settings ----------------------------------------------------------
TITLE = "The Reading Nook | Customer Feedback"
CSV_FILE = "feedback.csv"
LABEL_NAMES = {
    "book_availability": "Book availability & selection",
    "staff_service": "Staff service",
    "store_atmosphere": "Store atmosphere",
    "pricing_value": "Pricing & value",
    "events_community": "Events & community",
    "other": "Other / unclear topic",
    "unclear": "Needs label review",
    "no_comment": "Rating only (no comment)",
}
LABEL_COLORS = {
    "book_availability": "#4776A8",
    "staff_service": "#2A9D8F",
    "store_atmosphere": "#E9C46A",
    "pricing_value": "#F4A261",
    "events_community": "#8E7DBE",
    "other": "#A0A0A0",
    "unclear": "#C44536",
    "no_comment": "#D0D0D0",
}
COLUMNS = ["comment", "rating", "label", "manual_review", "review_reason"]
# ------------------------------------------------------------------------

st.set_page_config(page_title=TITLE, page_icon="📚", layout="wide")
st.title("📚 The Reading Nook")
st.caption(
    "An independent bookstore feedback demo. Customer comments are categorized with an LLM "
    "so the owner can identify what to improve."
)
st.info(
    "Business question: What parts of the bookstore experience should the owner prioritize "
    "improving to better serve customers?"
)

# Load saved feedback, or start with an empty table.
if os.path.exists(CSV_FILE):
    try:
        df = pd.read_csv(CSV_FILE).reindex(columns=COLUMNS)
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        df = pd.DataFrame(columns=COLUMNS)
else:
    df = pd.DataFrame(columns=COLUMNS)

# Normalize values from the CSV so filtering works consistently.
if not df.empty:
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["comment"] = df["comment"].fillna("").astype(str)
    df["label"] = df["label"].fillna("unclear").astype(str)
    df["manual_review"] = df["manual_review"].fillna(False).astype(str).str.lower().isin(["true", "1", "yes"])
    df["review_reason"] = df["review_reason"].fillna("").astype(str)

tab_customer, tab_owner = st.tabs(["Customer: leave feedback", "Owner: analyze feedback"])

# ---- Customer side -----------------------------------------------------
with tab_customer:
    st.subheader("Tell us about your visit")
    st.write("Your rating, comment, or both can help us improve the bookstore.")
    with st.form("feedback_form", clear_on_submit=True):
        stars = st.feedback("stars")  # None until clicked; then 0 through 4.
        comment = st.text_area(
            "What would you like us to know? (Optional if you leave a star rating)",
            placeholder="For example: I loved the staff recommendations, but the book I wanted was out of stock.",
        )
        submitted = st.form_submit_button("Send feedback")

    if submitted:
        clean_comment = comment.strip()
        if not clean_comment and stars is None:
            st.error("Please leave a star rating, a written comment, or both.")
        else:
            rating = stars + 1 if stars is not None else None
            label = "no_comment"
            review_reasons = []
            if clean_comment:
                try:
                    with st.spinner("Categorizing your comment..."):
                        label = label_comment(clean_comment)
                except Exception as exc:
                    label = "unclear"
                    review_reasons.append("Automatic labeling failed; check the comment manually.")
                    st.warning(f"The comment was saved, but automatic labeling failed ({type(exc).__name__}).")

                if label == "unclear":
                    review_reasons.append("The LLM did not return a recognized label.")
                elif label == "other":
                    review_reasons.append("The comment may need a more specific category.")

            if rating is not None and rating <= 2:
                review_reasons.append("Low star rating (1–2 stars); consider follow-up.")

            new_row = pd.DataFrame([{
                "comment": clean_comment,
                "rating": rating,
                "label": label,
                "manual_review": bool(review_reasons),
                "review_reason": " ".join(dict.fromkeys(review_reasons)),
            }], columns=COLUMNS)
            updated = pd.concat([df, new_row], ignore_index=True)
            updated.to_csv(CSV_FILE, index=False)
            df = updated
            st.success("Thank you! Your feedback has been saved.")
            if clean_comment:
                st.caption(f"For the demo, the comment was categorized as: **{LABEL_NAMES.get(label, label)}**")

    with st.expander("How comments are categorized"):
        st.markdown(
            "- **Book availability & selection:** Stock, selection, and special orders.\n"
            "- **Staff service:** Helpfulness, knowledge, and friendliness.\n"
            "- **Store atmosphere:** Layout, comfort, cleanliness, and browsing experience.\n"
            "- **Pricing & value:** Prices, discounts, and value for money.\n"
            "- **Events & community:** Author talks, book clubs, and community activities.\n"
            "- **Other / unclear topic:** Anything outside these categories or too vague to classify."
        )

# ---- Owner side --------------------------------------------------------
with tab_owner:
    st.subheader("What should the bookstore prioritize?")
    st.caption("Use the category patterns and low ratings to decide where to investigate first.")
    if df.empty:
        st.info("No feedback yet. Switch to the customer tab and submit the first rating or comment.")
    else:
        comment_mask = df["comment"].str.strip().ne("")
        commented = df[comment_mask].copy()
        review_mask = df["manual_review"].astype(bool)
        avg_rating = df["rating"].dropna().mean()
        low_ratings = int((df["rating"].dropna() <= 2).sum())

        m1, m2, m3 = st.columns(3)
        m1.metric("Total feedback entries", len(df))
        m2.metric("Average star rating", f"{avg_rating:.1f} / 5" if pd.notna(avg_rating) else "N/A")
        m3.metric("Comments needing manual review", int(review_mask.sum()))
        st.caption(f"Low ratings (1–2 stars): {low_ratings}. These are included in manual review.")

        left, right = st.columns(2)
        with left:
            st.caption("What customers are talking about")
            if commented.empty:
                st.info("No written comments yet, so there are no category counts to chart.")
            else:
                counts = commented["label"].map(lambda x: LABEL_NAMES.get(x, x)).value_counts().rename_axis("Category").reset_index(name="Comments")
                fig = px.bar(counts, x="Category", y="Comments", color="Category", text="Comments")
                fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Number of comments")
                fig.update_xaxes(tickangle=-25)
                st.plotly_chart(fig, use_container_width=True)

        with right:
            st.caption("Average star rating by comment category")
            rated_comments = commented.dropna(subset=["rating"]).copy()
            if rated_comments.empty:
                st.info("No written comments with star ratings yet.")
            else:
                rated_comments["Category"] = rated_comments["label"].map(lambda x: LABEL_NAMES.get(x, x))
                avg_by_label = rated_comments.groupby("Category", as_index=False)["rating"].mean()
                avg_by_label["rating"] = avg_by_label["rating"].round(2)
                fig = px.bar(avg_by_label, x="Category", y="rating", color="Category", text="rating", range_y=[0, 5])
                fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Average stars (out of 5)")
                fig.update_xaxes(tickangle=-25)
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("Comments needing manual review")
        st.caption(
            "A comment is listed here if its label is unclear, it falls into Other, automatic labeling failed, "
            "or its star rating is 1–2. Full comments are shown so the owner can understand the context."
        )
        to_review = df[review_mask].copy()
        if to_review.empty:
            st.success("No comments are currently flagged for manual review.")
        else:
            for idx, row in to_review.iterrows():
                rating_text = f"{int(row['rating'])} / 5 stars" if pd.notna(row["rating"]) else "No star rating"
                label_text = LABEL_NAMES.get(row["label"], row["label"])
                with st.container(border=True):
                    st.markdown(f"**Feedback #{idx + 1} · {rating_text} · {label_text}**")
                    st.write(row["comment"] if row["comment"].strip() else "No written comment was provided.")
                    st.caption(f"Reason for review: {row['review_reason'] or 'Please verify this entry.'}")

        with st.expander("All saved feedback"):
            display_df = df.copy()
            display_df["label"] = display_df["label"].map(lambda x: LABEL_NAMES.get(x, x))
            st.dataframe(display_df, hide_index=True, use_container_width=True)
        st.download_button(
            "Download feedback CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="feedback.csv",
            mime="text/csv",
        )
        st.caption(
            "Deployment note: Streamlit Cloud's local filesystem is not durable storage. Download the CSV to keep a copy; "
            "entries may disappear when the app restarts or redeploys."
        )
