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
from fpdf import FPDF
import time  # For simulating processing time

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
        textbook1_name = names[0]
        textbook2_name = names[1]

        full_prompt = (
    f"Conduct a comparative analysis of the following two textbooks. The first textbook is '{textbook1_name}', and the second textbook is '{textbook2_name}'. This analysis is intended for educators, curriculum developers, and parents to evaluate how well '{textbook2_name}' aligns with NCERT guidelines:\n\n"
    f"Textbook 1 ({textbook1_name}):\n{texts[0]}\n\n"
    f"Textbook 2 ({textbook2_name}):\n{texts[1]}\n\n"
    "Provide a detailed analysis of each chapter in '{textbook2_name}', focusing on its alignment with NCERT guidelines. For each chapter, address the following:\n\n"
    "  {chapter_name} - Alignment with NCERT Guidelines**:\n"
    "  1. What are the strengths of the chapter '{chapter_name}' in terms of content coverage, clarity, relevance to learning objectives, and use of age-appropriate examples?provide atleast six to ten points \n"
    "  2. Provide constructive suggestions for improving '{chapter_name}', including additional pictures, activities, exercises, and examples that could be added to better align with NCERT guidelines.\n"
    "  3. Give specific and age-appropriate examples that could help enhance the understanding of six-year-old children.\n"
    "  4. Identify any unique elements in '{chapter_name}' that make it particularly effective for achieving the NCERT learning objectives.\n\n"
    "  5. Overall, summarize the alignment of '{textbook2_name}' with NCERT guidelines, focusing on how its chapters provide a valuable learning experience while adhering to NCERT standards."
    "  6. List all the diffcult words used in this books chapter that can be diffcult to understand by the six to seven years old children or class 1 students also give me the suggestion to replace those difficult words."
)

    
        logger.info(f"Sending comparison prompt to Gemini: {full_prompt}")  
        response = chat.send_message(full_prompt, stream=True)
        response.resolve()
        comparisons = response.text
        logger.info(f"Received comparison response from Gemini: {comparisons}")  
    else:
        comparisons = "Error: Need exactly two textbooks for comparison."
    
    return comparisons

# Function to save comparison result to a PDF
def save_comparison_to_pdf(comparison_text, file_name="comparison_result.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Split the text into lines to fit into the PDF
    lines = comparison_text.split('\n')
    for line in lines:
        pdf.multi_cell(0, 10, line)
    
    pdf.output(file_name)
    logger.info(f"Comparison result saved to {file_name}")

# Initialize Streamlit app with layout
st.set_page_config(page_title="Suggestion to ATC publishers class 1 value education based on NCERT guidelines")

# Custom CSS for various design elements
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(135deg, #ffafbd, #ffc3a0);  /* Animated gradient background */
        animation: gradient 15s ease infinite;
    }

    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .hover-button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border: none;
        cursor: pointer;
        transition-duration: 0.4s;
    }

    .hover-button:hover {
        background-color: white;
        color: black;
        border: 2px solid #4CAF50;
    }

    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted black;
    }

    .tooltip .tooltiptext {
        visibility: hidden;
        width: 120px;
        background-color: black;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 100%;
        left: 50%;
        margin-left: -60px;
        opacity: 0;
        transition: opacity 0.3s;
    }

    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }

    .fade-in {
        opacity: 0;
        animation: fadeIn ease 2s;
        animation-fill-mode: forwards;
    }

    @keyframes fadeIn {
        0% { opacity:0; }
        100% { opacity:1; }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit app title with fade-in effect
st.markdown("<h1 class='fade-in' style='color: #4CAF50;'>Suggestion to ATC publishers Scope 2 value education book class 1 based on NCERT guidelines</h1>", unsafe_allow_html=True)

# Sidebar layout for file upload, submit button, and logo
with st.sidebar:
    st.image(r"c:\Users\SPURGE\Downloads\looooogooooo.jpg", use_column_width=True)  
    st.subheader("Upload your textbooks:")
    uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)
    submit = st.button("Process the files", key="process_button", help="Click to start processing")

# Main content
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'textbook_chunks' not in st.session_state:
    st.session_state['textbook_chunks'] = []
if 'textbook_names' not in st.session_state:
    st.session_state['textbook_names'] = []

if uploaded_files and submit:
    with st.spinner("Processing... Please wait while we extract and process the PDFs."):
        # Animated progress bar
        st.markdown("<h2 style='color: #4CAF50;'>Processing PDF Files...</h2>", unsafe_allow_html=True)
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Simulate time taken to process the files
        pdf_texts = []
        pdf_names = []

        for uploaded_file in uploaded_files:
            for i in range(100):
                progress_bar.progress(i + 1)
                status_text.text(f"Processing... {i+1}%")
                time.sleep(0.05)  # Simulate processing time

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

        if len(pdf_texts) == 2:
            st.session_state['textbook_chunks'] = [chunk_text(text) for text in pdf_texts]
            st.session_state['textbook_names'] = pdf_names

            st.success("Processing Complete!")
        else:
            st.error("Please upload exactly two textbooks for comparison.")

# Once files are processed, display comparison
if st.session_state['textbook_chunks'] and st.session_state['textbook_names']:
    comparison_result = compare_textbooks(st.session_state['textbook_chunks'], st.session_state['textbook_names'])
    st.markdown(f"### Textbook 1: {st.session_state['textbook_names'][0]}")
    st.markdown(f"### Textbook 2: {st.session_state['textbook_names'][1]}")
    st.markdown(comparison_result)

    # Offer download of comparison as a PDF
    save_file = st.button("Download Comparison Result as PDF")
    if save_file:
        save_comparison_to_pdf(comparison_result)
        st.markdown("Download the PDF [here](comparison_result.pdf).")
