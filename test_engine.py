import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import base64

# Set page configuration
st.set_page_config(page_title="PMP Practice Exam", layout="wide")

# Load the Excel file
@st.cache_data
def load_data():
    excel_file = "PMP Practice Exam Question Bank_Update 2023 (1).xlsx"
    sheets = {
        "Core 260": "Core 260",
        "25 Q1 2023": "25 Q1 2023",
        "25 Q4 2022": "25 Q4 2022",
        "55 Q2 2021": "55 Q2 2021"
    }
    return {name: pd.read_excel(excel_file, sheet_name=sheet) for name, sheet in sheets.items()}

def format_time(seconds):
    """Format seconds into hours:minutes:seconds"""
    return str(timedelta(seconds=int(seconds)))

# Initialize session state variables
if 'page' not in st.session_state:
    st.session_state.page = "intro"
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'question_times' not in st.session_state:
    st.session_state.question_times = {}
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'current_question_start_time' not in st.session_state:
    st.session_state.current_question_start_time = None
if 'selected_test' not in st.session_state:
    st.session_state.selected_test = None
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = {}
if 'answered_questions' not in st.session_state:
    st.session_state.answered_questions = set()

# Create callback functions for buttons
def handle_start_quiz():
    st.session_state.page = "quiz"
    st.session_state.start_time = time.time()
    st.session_state.current_question_start_time = time.time()

def handle_next_question():
    # Get the current question data
    data = load_data()
    test_data = data[st.session_state.selected_test]
    question_row = test_data.iloc[st.session_state.current_question]
    
    # Get user answer from session state
    user_answer = st.session_state[f"q{st.session_state.current_question}"]
    
    # Save time for current question
    question_time = time.time() - st.session_state.current_question_start_time
    st.session_state.question_times[st.session_state.current_question] = question_time
    
    # Check answer
    correct_answer = question_row['Key']
    option_map = {
        'A': question_row['Option A'],
        'B': question_row['Option B'],
        'C': question_row['Option C'],
        'D': question_row['Option D']
    }
    
    # Save answer and update score
    st.session_state.answers[st.session_state.current_question] = user_answer
    if user_answer == option_map.get(correct_answer):
        if st.session_state.current_question not in st.session_state.question_times or st.session_state.question_times.get(st.session_state.current_question) == 0:
            st.session_state.score += 1
    
    # Move to next question or finish
    st.session_state.current_question += 1
    # Reset show_answer for the next question
    if st.session_state.current_question not in st.session_state.show_answer:
        st.session_state.show_answer[st.session_state.current_question] = False
    
    if st.session_state.current_question >= len(test_data):
        st.session_state.page = "results"
    else:
        st.session_state.current_question_start_time = time.time()

def handle_prev_question():
    # Save time for current question
    question_time = time.time() - st.session_state.current_question_start_time
    st.session_state.question_times[st.session_state.current_question] = question_time
    
    # Move to previous question
    st.session_state.current_question -= 1
    st.session_state.current_question_start_time = time.time()

def handle_restart_quiz():
    st.session_state.page = "intro"
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.answers = {}
    st.session_state.question_times = {}
    st.session_state.start_time = None
    st.session_state.current_question_start_time = None
    st.session_state.show_answer = {}
    st.session_state.answered_questions = set()

def handle_show_answer():
    # Mark this question as answered
    st.session_state.answered_questions.add(st.session_state.current_question)
    # Show the answer
    st.session_state.show_answer[st.session_state.current_question] = True

# Add an auto-refresh component
def autorefresh_component():
    # Create JavaScript to reload the page
    js_code = """
    <script>
    if (window.top.location.pathname === '/') {
        window.parent.location.reload();
    }
    </script>
    """
    st.components.v1.html(js_code, height=0)

# INTRODUCTION PAGE
if st.session_state.page == "intro":
    st.title("PMP Practice Exam")
    st.write("Welcome to the PMP Practice Exam. This quiz will test your knowledge of project management principles.")
    
    # Load data for test selection
    data = load_data()
    
    # Test selection
    test_name = st.selectbox("Select Test", list(data.keys()))
    st.session_state.selected_test = test_name
    
    # Instructions section
    st.subheader("Instructions:")
    col1, col2 = st.columns(2)
    with col1:
        st.write("1. Select the appropriate answer for each question.")
        st.write("2. Use the Next and Previous buttons to navigate through the quiz.")
    with col2:
        st.write("3. Click 'Answer' to see the correct answer.")
        st.write("4. You can only proceed to the next question after viewing the answer.")
        
    # Add the start button to the instruction section
    st.button("Start Quiz", type="primary", key="start_btn", on_click=handle_start_quiz)

# QUIZ PAGE
elif st.session_state.page == "quiz":
    # Load data
    data = load_data()
    test_data = data[st.session_state.selected_test]
    
    # Quiz header with timer
    col_header, col_timer = st.columns([3, 1])
    with col_header:
        st.title(f"PMP Practice Exam - {st.session_state.selected_test}")
    with col_timer:
        elapsed_time = time.time() - st.session_state.start_time
        st.info(f"Total quiz time: {format_time(elapsed_time)}")
    
    # Display current question
    if st.session_state.current_question < len(test_data):
        question_row = test_data.iloc[st.session_state.current_question]
        
        # Question header with timer
        col_q, col_q_timer = st.columns([3, 1])
        with col_q:
            st.subheader(f"Question {st.session_state.current_question + 1} of {len(test_data)}")
            st.write(question_row['Question'])
        with col_q_timer:
            question_time = time.time() - st.session_state.current_question_start_time
            st.info(f"Time on question: {format_time(question_time)}")
        
        # Answer options
        options = [question_row['Option A'], question_row['Option B'], question_row['Option C'], question_row['Option D']]
        st.radio("Select your answer:", options, key=f"q{st.session_state.current_question}")
        
        # Get correct answer for display
        correct_key = question_row['Key']
        correct_option = question_row[f'Option {correct_key}']
        
        # Show answer button and feedback
        answer_col, feedback_col = st.columns([1, 3])
        with answer_col:
            st.button("Show Answer", key=f"answer_btn_{st.session_state.current_question}", 
                     on_click=handle_show_answer)
            
        with feedback_col:
            # Check if we should show the answer
            if st.session_state.current_question in st.session_state.answered_questions:
                user_answer = st.session_state.get(f"q{st.session_state.current_question}")
                is_correct = user_answer == correct_option
                
                if is_correct:
                    st.success(f"✓ Correct! The answer is: {correct_key}) {correct_option}")
                else:
                    st.error(f"✗ Incorrect. The correct answer is: {correct_key}) {correct_option}")
                
                # Explanation if available
                if 'Explanation' in question_row and pd.notna(question_row['Explanation']):
                    st.info(f"Explanation: {question_row['Explanation']}")
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            prev_disabled = st.session_state.current_question == 0
            st.button("Previous", disabled=prev_disabled, key="prev_btn", on_click=handle_prev_question)
        
        with col3:
            next_label = "Next" if st.session_state.current_question < len(test_data) - 1 else "Finish Quiz"
            # Only enable Next button if answer has been shown
            next_disabled = st.session_state.current_question not in st.session_state.answered_questions
            st.button(next_label, key="next_btn", on_click=handle_next_question, disabled=next_disabled)

# RESULTS PAGE
elif st.session_state.page == "results":
    data = load_data()
    test_data = data[st.session_state.selected_test]
    
    st.title("Quiz Results")
    
    # Calculate total time
    total_time = time.time() - st.session_state.start_time
    
    # Display results
    st.success(f"Your score: {st.session_state.score}/{len(test_data)} ({int(st.session_state.score/len(test_data)*100)}%)")
    st.info(f"Total time: {format_time(total_time)}")
    
    # Calculate average time per question
    avg_time = total_time / len(test_data)
    st.info(f"Average time per question: {format_time(avg_time)}")
    
    # Restart button
    st.button("Restart Quiz", key="restart_btn", on_click=handle_restart_quiz) 