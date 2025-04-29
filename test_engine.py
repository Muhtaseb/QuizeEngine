import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

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

# Handle page navigation logic
def start_quiz():
    st.session_state.page = "quiz"
    st.session_state.start_time = time.time()
    st.session_state.current_question_start_time = time.time()

def next_question(question_row, user_answer):
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
    data = load_data()
    test_data = data[st.session_state.selected_test]
    st.session_state.current_question += 1
    if st.session_state.current_question >= len(test_data):
        st.session_state.page = "results"
    else:
        st.session_state.current_question_start_time = time.time()

def prev_question():
    # Save time for current question
    question_time = time.time() - st.session_state.current_question_start_time
    st.session_state.question_times[st.session_state.current_question] = question_time
    
    # Move to previous question
    st.session_state.current_question -= 1
    st.session_state.current_question_start_time = time.time()

def restart_quiz():
    st.session_state.page = "intro"
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.answers = {}
    st.session_state.question_times = {}
    st.session_state.start_time = None
    st.session_state.current_question_start_time = None

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
        st.write("3. Your score and time will be shown at the end of the quiz.")
        st.write("4. Click 'Start Quiz' when you're ready to begin.")
        # Add the start button to the instruction section
        if st.button("Start Quiz", type="primary", key="start_btn"):
            start_quiz()
            st.rerun()

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
        user_answer = st.radio("Select your answer:", options, key=f"q{st.session_state.current_question}")
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            prev_disabled = st.session_state.current_question == 0
            if st.button("Previous", disabled=prev_disabled, key="prev_btn"):
                prev_question()
                st.rerun()
        
        with col2:
            next_label = "Next" if st.session_state.current_question < len(test_data) - 1 else "Finish Quiz"
            if st.button(next_label, key="next_btn"):
                next_question(question_row, user_answer)
                st.rerun()
        
        # Timer refresh
        placeholder = st.empty()
        time.sleep(0.9)
        st.rerun()

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
    if st.button("Restart Quiz", key="restart_btn"):
        restart_quiz()
        st.rerun() 
   