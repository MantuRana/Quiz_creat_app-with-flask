from flask import Flask, request, render_template, redirect, url_for, session
import fitz  # PyMuPDF
import re
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Set the folder for storing uploaded PDFs
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Function to extract questions, options, and answers from a PDF
def extract_questions_answers(pdf_path):
    doc = fitz.open(pdf_path)
    all_text = ""

    # Extract text from each page
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        all_text += page.get_text()

    # Define the regular expression for matching questions, options, and answers
    question_pattern = r'(\d+)\.\s(.+?)(A\..+?D\..+?)(ANSWER:\s[A-Z])'
    matches = re.findall(question_pattern, all_text, re.DOTALL)

    qa_pairs = []

    # Process each matched question, options, and answer
    for match in matches:
        question_number = match[0]
        question_text = match[1].strip()
        options = match[2].strip()
        answer = match[3].replace("ANSWER: ", "").strip()

        qa_pairs.append({
            "Question": f"Q{question_number}: {question_text}",
            "Options": options,
            "Answer": answer
        })

    return qa_pairs

# Store extracted questions globally (in-memory)
qa_pairs = []

# Route for the homepage (upload form)
@app.route('/')
def index():
    return render_template('index.html')

# Route for uploading the PDF and extracting questions
@app.route('/upload', methods=['POST'])
def upload_file():
    global qa_pairs
    file = request.files['file']

    if file:
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(pdf_path)
        qa_pairs = extract_questions_answers(pdf_path)

        # Reset session counters
        session['correct'] = 0
        session['wrong'] = 0

        return redirect(url_for('quiz', question_num=1))

    return redirect(url_for('index'))

# Route for displaying the quiz
@app.route('/quiz/<int:question_num>', methods=['GET', 'POST'])
def quiz(question_num):
    global qa_pairs

    # Check if all questions have been answered
    if question_num > len(qa_pairs):
        correct_count = session.get('correct', 0)
        wrong_count = session.get('wrong', 0)
        return f"Quiz finished! Correct: {correct_count}, Wrong: {wrong_count}"

    feedback = ""
    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip().upper()
        correct_answer = qa_pairs[question_num - 1]['Answer']

        # Check if the answer is correct or wrong
        if user_answer == correct_answer:
            feedback = "Correct!"
            session['correct'] += 1
        else:
            feedback = f"Wrong! The correct answer is: {correct_answer}"
            session['wrong'] += 1

    # Return the current quiz question
    return render_template('quiz.html', qa=qa_pairs[question_num - 1], feedback=feedback, question_num=question_num)

# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)
