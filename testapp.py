import os
import io
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
import google.generativeai as genai
from dotenv import load_dotenv
import pdfplumber
import logging

# Load environment variables
load_dotenv()

# Configure Gemini API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Gemini Pro model
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(file):
    text = ""
    
    
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                # Extract text with layout consideration
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                
               
                if not page_text.strip():
                    page_image = page.to_image()
                    ocr_text = pytesseract.image_to_string(page_image.original, config='--psm 6')
                    text += ocr_text
                    
    except Exception as e:
        logger.error(f"pdfplumber failed: {e}")
        logger.info("Falling back to PyMuPDF for text extraction.")
        
        # Fall back to PyMuPDF if pdfplumber fails
        file.seek(0)  
        pdf_document = fitz.open(stream=file.read(), filetype="pdf")

        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            
            page_text = page.get_text("text")
            text += page_text

            
            if not page_text.strip():
                image_list = page.get_images(full=True)
                for image_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    
                    ocr_text = pytesseract.image_to_string(image, config='--psm 6')
                    text += ocr_text

    return text


def chunk_text(text, chunk_size=10000, chunk_overlap=1000):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return text_splitter.split_text(text)


def get_gemini_response(question, context_chunks, textbook_name):
    responses = []
    for chunk in context_chunks:
        full_prompt = f"Context from {textbook_name}:\n{chunk}\n\nBased on the above context, please answer the following question:\n\n{question}"
        response = chat.send_message(full_prompt, stream=True)
        response.resolve()  
        responses.append(response)
    
    combined_response = " ".join(response.text for response in responses)
    
    return combined_response.strip()


def compare_textbooks(texts, names):
    if len(texts) == 2:
        full_prompt = (
            f"Compare the following two textbooks and determine which one is better based on their content.\n\n"
            f"Textbook 1 ({names[0]}):\n{texts[0]}\n\n"
            f"Textbook 2 ({names[1]}):\n{texts[1]}\n\n"
            "Provide a detailed analysis including which textbook has better coverage of topics, clarity of explanations, accuracy of information, "
            "and overall quality of the content. Additionally, consider how well each textbook addresses the subject matter and its usefulness for learning."
        )
        response = chat.send_message(full_prompt, stream=True)
        response.resolve()  # Wait for the response to complete
        comparisons = response.text
    else:
        comparisons = "Error: Need exactly two textbooks for comparison."
    
    return comparisons

# Initialize Streamlit app
st.set_page_config(page_title="Textbook Comparison Bot")
st.header("Textbook Comparison Bot")

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    pdf_texts = []
    pdf_names = []

    for uploaded_file in uploaded_files:
        logger.info(f"Processing file: {uploaded_file.name}")
        try:
            uploaded_file.seek(0)  # Reset file stream position
            pdf_text = extract_text_from_pdf(uploaded_file)
            
            if pdf_text.strip():  # Check if text extraction was successful
                pdf_texts.append(pdf_text)
                pdf_names.append(uploaded_file.name)
            else:
                st.write(f"Text extraction failed for {uploaded_file.name}.")
                logger.warning(f"Text extraction failed for {uploaded_file.name}.")
        except Exception as e:
            st.write(f"Error processing {uploaded_file.name}: {e}")
            logger.error(f"Error processing {uploaded_file.name}: {e}")
    
    st.write("PDF Texts:", pdf_texts)
    st.write("PDF Names:", pdf_names)
    
    try:
        if len(pdf_texts) == 2:  # Ensure exactly two PDFs are uploaded
            # Chunk each textbook's text separately
            textbook_chunks = [chunk_text(text) for text in pdf_texts]
            textbook_names = pdf_names

            comparisons = compare_textbooks(pdf_texts, textbook_names)
            st.subheader("Comparison Result:")
            st.write(comparisons)

            selected_textbook = st.selectbox("Select Textbook to Query", options=pdf_names)
            input_text = st.text_input("Input your question:", key="input")
            submit = st.button("Ask the question")

            if submit and input_text:
                # Find the index of the selected textbook
                selected_index = textbook_names.index(selected_textbook)
                selected_chunks = textbook_chunks[selected_index]

                if selected_chunks:
                    response = get_gemini_response(input_text, selected_chunks, selected_textbook)
                    st.session_state['chat_history'].append(("You", input_text))
                    st.subheader("The Response is")
                    st.write(response)
                    st.session_state['chat_history'].append(("Bot", response))
                else:
                    st.write(f"The context chunks for {selected_textbook} are empty. Please upload a valid PDF.")
        else:
            st.write("Please upload exactly two PDF documents for comparison.")
    except Exception as e:
        st.write(f"Error: {e}")
        logger.error(f"Error during comparison: {e}")

st.subheader("Chat History")
for role, text in st.session_state['chat_history']:
    st.write(f"{role}: {text}")
