import os
import requests
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()

st.set_page_config(
    page_title="SimplifyAI",
    page_icon="📚",
    layout="wide"
)

st.title("📚 SimplifyAI")
st.subheader("Make complex learning content simple.")

st.write(
    "Upload academic material or paste text. "
    "IBM Granite will help simplify it for your learning level."
)

# Read IBM credentials
API_KEY = os.getenv("IBM_API_KEY")
PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
URL = os.getenv("WATSONX_URL")
MODEL_ID = os.getenv("MODEL_ID")

# Read uploaded file
uploaded_file = st.file_uploader(
    "Upload your study material",
    type=["pdf", "txt"]
)

text_input = st.text_area(
    "Or paste your academic content here",
    height=200
)

level = st.selectbox(
    "Choose your learning level",
    ["Beginner", "Intermediate", "Advanced"]
)

language = st.selectbox(
    "Choose output language",
    ["English", "Hindi"]
)

output_format = st.selectbox(
    "Choose output format",
    ["Simple Explanation", "Bullet Points", "Study Notes"]
)


def extract_text(file):
    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        return "\n".join(
            page.extract_text() or "" for page in reader.pages
        )

    return file.getvalue().decode("utf-8", errors="ignore")


def get_iam_token(api_key):
    response = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key
        },
        timeout=30
    )

    response.raise_for_status()
    return response.json()["access_token"]


def simplify_content(content):
    token = get_iam_token(API_KEY)

    prompt = f"""
Simplify the following academic content.

Learning level: {level}
Output language: {language}
Output format: {output_format}

Instructions:
- Explain difficult terms in simple language.
- Preserve important facts and concepts.
- Use clear headings and examples where useful.
- Do not invent information.
- If something is unclear in the source, mention it.

Academic content:
{content}
"""

    response = requests.post(
        f"{URL.rstrip('/')}/ml/v1/text/chat?version=2024-05-31",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        json={
            "model_id": MODEL_ID,
            "project_id": PROJECT_ID,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_completion_tokens": 1200
        },
        timeout=120
    )

    response.raise_for_status()
    result = response.json()

    return result["choices"][0]["message"]["content"]


# Generate simplified content
if st.button("Simplify Content", type="primary"):

    content = text_input.strip()

    if uploaded_file is not None:
        content = extract_text(uploaded_file).strip()

    if not content:
        st.warning("Please upload a file or enter some content.")

    elif not all([API_KEY, PROJECT_ID, URL, MODEL_ID]):
        st.error("IBM watsonx.ai credentials are not configured.")

    else:
        try:
            with st.spinner("IBM Granite is simplifying your content..."):
                result = simplify_content(content)

            st.success("Content simplified successfully!")
            st.markdown("### Your Simplified Content")
            st.markdown(result)

            st.download_button(
                "Download Simplified Notes",
                data=result,
                file_name="simplified_notes.txt",
                mime="text/plain"
            )

        except requests.exceptions.RequestException as error:
            st.error(f"IBM API request failed: {error}")

        except Exception as error:
            st.error(f"Something went wrong: {error}")