# The Reading Nook: customer feedback app

This Streamlit app is a small customer-feedback demo for an independent bookstore. Customers can submit a star rating, a written comment, or both. Written comments are categorized by an LLM using Groq; the app saves the comment, rating, category, and manual-review flag to `feedback.csv`.

## Business question

**What parts of the bookstore experience should the owner prioritize improving to better serve customers?**

## Labels

- `book_availability`: Stock, selection, and special orders.
- `staff_service`: Staff helpfulness, knowledge, friendliness, and responsiveness.
- `store_atmosphere`: Layout, comfort, cleanliness, noise, and browsing experience.
- `pricing_value`: Prices, discounts, loyalty offers, and value for money.
- `events_community`: Author talks, book clubs, children's activities, and community events.
- `other`: Feedback outside the categories or too vague to classify.

Every written comment receives exactly one label. The app flags entries for manual review when the LLM label is unclear, the category is `other`, labeling fails, or the star rating is 1–2. The owner dashboard includes three key metrics, two charts, and the full text of flagged comments.

## Files

- `app.py`: Customer form and owner dashboard.
- `labeler.py`: Calls the Groq chat-completions API to classify comments.
- `requirements.txt`: Dependencies installed by Streamlit Cloud.

## Run locally

1. Install the dependencies: `pip install -r requirements.txt`
2. Create `.streamlit/secrets.toml` with this content:

   ```toml
   GROQ_API_KEY = "your-groq-api-key"
   ```

3. Run: `streamlit run app.py`

Never commit `.streamlit/secrets.toml` or your API key to GitHub.

## Deploy to Streamlit Community Cloud

1. Create a **public GitHub repository** and upload `app.py`, `labeler.py`, and `requirements.txt`.
2. In Streamlit Community Cloud, create an app from that repository and set the main file path to `app.py`.
3. In the app's **Settings / Secrets**, add `GROQ_API_KEY = "your-groq-api-key"` (TOML format). Do not put the key in your repository.
4. Deploy the app.

The model name is set in `labeler.py` as `openai/gpt-oss-20b`. If Groq retires or changes model availability, select a currently supported model from Groq's model documentation and update `MODEL`.

## Storage note

This starter saves entries to a local `feedback.csv`. On Streamlit Cloud, local files are not durable storage and can disappear on restart or redeploy. Use the dashboard's Download feedback CSV button to retain a copy.
