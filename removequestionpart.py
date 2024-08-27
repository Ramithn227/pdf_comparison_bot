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

# Function to extract text from a PDF using PyMuPDF and pdfplumber with OCR for images
def extract_text_from_pdf(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
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

# Function to chunk text using RecursiveCharacterTextSplitter
def chunk_text(text, chunk_size=10000, chunk_overlap=1000):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return text_splitter.split_text(text)

# Function to compare textbooks (PDFs) and include names
def compare_textbooks(texts, names):
    if len(texts) == 2:
        full_prompt = (
            f"Compare the following two textbooks and determine which one is better based on their content.\n\n"
            f"Textbook 1 ({names[0]}):\n{texts[0]}\n\n"
            f"Textbook 2 ({names[1]}):\n{texts[1]}\n\n"
            "1. **Topics Covered:** List the topics covered in each textbook point by point.\n"
            "2. **Clarity:** Analyze the clarity of explanations for each topic.\n"
            "3. **Accuracy:** Assess the accuracy of the information presented in each topic.\n"
            "4. **Depth of Coverage:** Evaluate the depth to which each topic is covered.\n"
            "5. **Usefulness for Learning:** Compare how useful each textbook is for learning the subject.\n"
            "6. **Additional Insights:** Identify any unique insights or additional information provided by each textbook.\n"
            "7. **Overall Comparison:** Provide an overall comparison, emphasizing that both textbooks are great resources.\n"
            "8. **Suggestions for Improvement:** Suggest any improvements or additional content that could be added to enhance both textbooks."
        )
        logger.info(f"Sending comparison prompt to Gemini: {full_prompt}")  
        response = chat.send_message(full_prompt, stream=True)
        response.resolve()
        comparisons = response.text
        logger.info(f"Received comparison response from Gemini: {comparisons}")  
    else:
        comparisons = "Error: Need exactly two textbooks for comparison."
    
    return comparisons

# Initialize Streamlit app with layout
st.set_page_config(page_title="Textbook Comparison Bot")
st.header("Textbook Comparison Bot")

# Sidebar layout for file upload, submit button, and logo
with st.sidebar:
    st.image(r"c:\Users\SPURGE\Downloads\logoo.jpg", use_column_width=True)  
    st.subheader("Upload your textbooks:")
    uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)
    submit = st.button("Process the files")

# Main content
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'textbook_chunks' not in st.session_state:
    st.session_state['textbook_chunks'] = []
if 'textbook_names' not in st.session_state:
    st.session_state['textbook_names'] = []

if uploaded_files and submit:
    pdf_texts = []
    pdf_names = []

    for uploaded_file in uploaded_files:
        logger.info(f"Processing file: {uploaded_file.name}")
        try:
            uploaded_file.seek(0)
            pdf_text = extract_text_from_pdf(uploaded_file)
            
            if pdf_text.strip():
                pdf_texts.append(pdf_text)
                pdf_names.append(uploaded_file.name)
            else:
                st.write(f"Text extraction failed for {uploaded_file.name}.")
                logger.warning(f"Text extraction failed for {uploaded_file.name}.")
        except Exception as e:
            st.write(f"Error processing {uploaded_file.name}: {e}")
            logger.error(f"Error processing {uploaded_file.name}: {e}")
    
    try:
        if len(pdf_texts) == 2:
            st.session_state['textbook_chunks'] = [chunk_text(text) for text in pdf_texts]
            st.session_state['textbook_names'] = pdf_names

            comparisons = compare_textbooks(pdf_texts, pdf_names)
            st.subheader("Comparison Result:")
            st.write(comparisons)
        else:
            st.write("Please upload exactly two PDF documents for comparison.")
    except Exception as e:
        st.write(f"Error: {e}")
        logger.error(f"Error during comparison: {e}")

st.subheader("Chat History")
for role, text in st.session_state['chat_history']:
    st.write(f"{role}: {text}")
