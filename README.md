📚 Textbook Comparison Bot
Textbook Comparison Bot is a user-friendly Streamlit web application that enables users to compare two textbooks (PDFs) based on various criteria. This tool leverages advanced natural language processing (NLP) through Google's Gemini Pro model to provide in-depth analysis and comparisons between the selected textbooks, helping users make informed decisions about their learning materials.

🚀 Features
Topic Coverage Comparison: Analyze the topics covered in both textbooks and compare them side by side.
Clarity & Accuracy Analysis: Assess how clearly and accurately each textbook presents its content.
Depth of Coverage: Evaluate the depth of the material covered, including how well concepts are explained.
Usefulness for Learning: Understand which textbook offers more value for learning purposes.
Additional Insights: Gain deeper insights such as examples, case studies, or real-world applications provided by the textbooks.
Natural Language Processing: Powered by Google's Gemini Pro NLP model for detailed, accurate comparisons.
🛠 Technologies Used
Streamlit: Fast, interactive web interface.
Python: Core programming language.
Google Gemini Pro Model: For powerful natural language processing and textbook analysis.
PyPDF2: For extracting text from PDF files.
pandas: Data manipulation and analysis.
MongoDB: For storing and retrieving user interaction data (optional, if needed).
📂 Installation
To run the project locally, follow these steps:

Clone the repository:

bash
Copy code
git clone https://github.com/your-username/textbook-comparison-bot.git
cd textbook-comparison-bot
Install the required dependencies:

bash
Copy code
pip install -r requirements.txt
Set up your environment variables by creating a .env file:

bash
Copy code
GOOGLE_API_KEY=your-google-api-key
Run the Streamlit application:

bash
Copy code
streamlit run app.py
📝 Usage
Upload two PDF textbooks using the app interface.
Select the criteria for comparison (topics, clarity, accuracy, depth, usefulness).
Click the "Compare" button to generate a detailed comparison based on the selected criteria.
View the generated analysis on the comparison page.
🔧 Requirements
Python 3.7+
Streamlit
PyPDF2
google-generativeai
pandas
dotenv
MongoDB (optional, for storing data)
📄 License
This project is licensed under the MIT License. See the LICENSE file for details.

🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

📧 Contact
If you have any questions or feedback, reach out at your-email@example.com.
