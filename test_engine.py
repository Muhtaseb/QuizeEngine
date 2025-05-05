import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import base64
from PIL import Image
import os
import io
from streamlit_autorefresh import st_autorefresh

# Set page configuration - MUST be the first Streamlit command
st.set_page_config(page_title="PMP Practice Exam", layout="wide")

# Auto-refresh every 1 second to update the timer (must come after set_page_config)
st_autorefresh(interval=1000, key="timer_refresh")

# Function to get image path for a question
def get_question_image_path(sheet_name, question_number):
    """
    Searches for an image file related to the current question in the Pictures folder structure.
    Returns the path if found, None otherwise.
    """
    # Define possible file name patterns
    possible_patterns = [
        f"Question {question_number}.png",
        f"Question{question_number}.png",
        f"Q{question_number}.png",
        f"Picture{question_number}.png",
        f"{question_number}.png"
    ]
    
    # Base directory for pictures
    base_dir = os.path.join("Pictures", sheet_name)
    
    # Check if the directory exists
    if not os.path.exists(base_dir):
        return None
        
    # Check for each possible pattern
    for pattern in possible_patterns:
        path = os.path.join(base_dir, pattern)
        if os.path.exists(path):
            return path
            
    return None

# Function to get image as base64 string
def get_image_as_base64(image_path):
    """Convert an image file to base64 string for display"""
    if not image_path or not os.path.exists(image_path):
        return None
    
    try:
        with open(image_path, "rb") as img_file:
            img_bytes = img_file.read()
            img_b64 = base64.b64encode(img_bytes).decode()
            return f"data:image/png;base64,{img_b64}"
    except Exception as e:
        st.warning(f"Error loading image {image_path}: {e}")
        return None

# Load the Excel file
@st.cache_data
def load_data():
    excel_file = "PMP Practice Exam Question Bank_Update 2023 (1).xlsx"
    sheets = {
        "Core 260": "Core 260",
        "25 Q1 2023": "25 Q1 2023",
        "25 Q4 2022": "25 Q4 2022",
        "55 Q2 2021": "55 Q2 2021",
        "Test": "Test"
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
if 'multi_select_answers' not in st.session_state:
    st.session_state.multi_select_answers = {}
if 'total_quiz_time' not in st.session_state:
    st.session_state.total_quiz_time = None

# Create callback functions for buttons
def handle_start_quiz():
    st.session_state.page = "quiz"
    st.session_state.start_time = time.time()
    st.session_state.current_question_start_time = time.time()

def handle_next_question():
    # Save time for current question
    question_time = time.time() - st.session_state.current_question_start_time
    st.session_state.question_times[st.session_state.current_question] = question_time
    
    # Move to next question or finish
    data = load_data()
    test_data = data[st.session_state.selected_test]
    
    # Safety check - make sure we don't go past the last question
    if st.session_state.current_question >= len(test_data) - 1:
        st.session_state.current_question = len(test_data) - 1
        # Save the total quiz time when finishing
        st.session_state.total_quiz_time = time.time() - st.session_state.start_time
        st.session_state.page = "results"
        return
        
    st.session_state.current_question += 1
    
    # Reset show_answer for the next question
    if st.session_state.current_question not in st.session_state.show_answer:
        st.session_state.show_answer[st.session_state.current_question] = False
    
    # Check if we need to go to results page
    if st.session_state.current_question >= len(test_data):
        # Save the total quiz time when finishing
        st.session_state.total_quiz_time = time.time() - st.session_state.start_time
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
    st.session_state.multi_select_answers = {}
    st.session_state.total_quiz_time = None

def handle_show_answer():
    # Mark this question as answered
    st.session_state.answered_questions.add(st.session_state.current_question)
    # Show the answer
    st.session_state.show_answer[st.session_state.current_question] = True
    
    # Score the question if not already scored
    if st.session_state.current_question not in st.session_state.answers:
        # Get current question data
        data = load_data()
        test_data = data[st.session_state.selected_test]
        question_row = test_data.iloc[st.session_state.current_question]
        
        # Check if this is a multiple-answer question
        correct_keys = str(question_row['Key']).split(',')
        correct_keys = [key.strip() for key in correct_keys]
        
        if len(correct_keys) > 1:
            # Multiple correct answers
            user_selections = st.session_state.multi_select_answers.get(st.session_state.current_question, [])
            
            # Map selected options back to keys
            option_to_key = {}
            for key in ['A', 'B', 'C', 'D', 'E']:
                option_col = f'Option {key}'
                if option_col in question_row and pd.notna(question_row[option_col]):
                    option_to_key[question_row[option_col]] = key
            
            user_selection_keys = []
            for selection in user_selections:
                key = option_to_key.get(selection)
                if key:
                    user_selection_keys.append(key)
            
            # Sort both lists for comparison
            user_selection_keys.sort()
            sorted_correct_keys = sorted(correct_keys)
            
            # Check if correct and update score
            is_correct = user_selection_keys == sorted_correct_keys
            if is_correct:
                st.session_state.score += 1
        else:
            # Single correct answer
            user_answer = st.session_state.get(f"q{st.session_state.current_question}")
            correct_key = correct_keys[0]
            
            # Check if the correct option column exists
            option_col = f'Option {correct_key}'
            if option_col in question_row and pd.notna(question_row[option_col]):
                correct_option = question_row[option_col]
                
                # Check if correct and update score
                is_correct = user_answer == correct_option
                if is_correct:
                    st.session_state.score += 1
        
        # Mark that we've scored this question
        st.session_state.answers[st.session_state.current_question] = True

# Function to handle multi-select changes
def update_multi_select():
    key = f"multi_q{st.session_state.current_question}"
    if key in st.session_state:
        selected_options = st.session_state[key]
        st.session_state.multi_select_answers[st.session_state.current_question] = selected_options
    else:
        # If the key doesn't exist yet, initialize with empty list
        st.session_state.multi_select_answers[st.session_state.current_question] = []

# Function to calculate time elapsed
def get_elapsed_time():
    if st.session_state.start_time is None:
        return 0
    return time.time() - st.session_state.start_time

def get_question_time():
    if st.session_state.current_question_start_time is None:
        return 0
    return time.time() - st.session_state.current_question_start_time

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
        st.write("1. Select the appropriate answer(s) for each question.")
        st.write("2. Use the Next and Previous buttons to navigate through the quiz.")
    with col2:
        st.write("3. Click 'Show Answer' to see the correct answer.")
        st.write("4. Some questions may have multiple correct answers.")
        st.write("5. You can only proceed to the next question after viewing the answer.")
        
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
        elapsed_time = get_elapsed_time()
        timer_placeholder = st.empty()
        timer_placeholder.info(f"Total quiz time: {format_time(elapsed_time)}")
    
    # Display current question
    if st.session_state.current_question < len(test_data):
        question_row = test_data.iloc[st.session_state.current_question]
        question_num = st.session_state.current_question + 1
        
        # Question header with timer
        col_q, col_q_timer = st.columns([3, 1])
        with col_q:
            st.subheader(f"Question {question_num} of {len(test_data)}")
            st.write(question_row['Question'])
            
            # Check for question image in the Pictures folder
            image_path = get_question_image_path(st.session_state.selected_test, question_num)
            if image_path:
                img_b64 = get_image_as_base64(image_path)
                if img_b64:
                    st.image(img_b64, caption=f"Question {question_num} Image")
                    
        with col_q_timer:
            question_time = get_question_time()
            question_timer_placeholder = st.empty()
            question_timer_placeholder.info(f"Time on question: {format_time(question_time)}")
        
        # Check if this is a multiple-answer question
        has_multiple_answers = ',' in str(question_row['Key'])
        
        # Get available options (check for Option E)
        options = []
        for key in ['A', 'B', 'C', 'D', 'E']:
            option_col = f'Option {key}'
            if option_col in question_row and pd.notna(question_row[option_col]):
                options.append(question_row[option_col])
        
        if has_multiple_answers:
            # For multiple answers, use multi-select checkbox
            st.write("**Select all that apply:**")
            try:
                selected = st.multiselect(
                    "Choose all correct answers:", 
                    options, 
                    key=f"multi_q{st.session_state.current_question}",
                    on_change=update_multi_select,
                    default=st.session_state.multi_select_answers.get(st.session_state.current_question, [])
                )
            except Exception as e:
                st.error(f"Error loading multiple choice options. Please try restarting the quiz.")
                st.session_state.multi_select_answers[st.session_state.current_question] = []
        else:
            # For single answer, use radio button
            try:
                st.radio("Select your answer:", options, key=f"q{st.session_state.current_question}")
            except Exception as e:
                st.error(f"Error loading answer options. Please try restarting the quiz.")
                
        # Create a single row of buttons for navigation and showing answers
        button_cols = st.columns([1, 1, 1, 2])  # Adding an extra column for spacing
        
        # Previous button
        with button_cols[0]:
            prev_disabled = st.session_state.current_question == 0
            st.button("Previous", disabled=prev_disabled, key="prev_btn", on_click=handle_prev_question)
        
        # Show Answer button
        with button_cols[1]:
            st.button("Show Answer", key=f"answer_btn_{st.session_state.current_question}", 
                     on_click=handle_show_answer)
        
        # Next button
        with button_cols[2]:
            next_label = "Next" if st.session_state.current_question < len(test_data) - 1 else "Finish Quiz"
            # Only enable Next button if answer has been shown
            next_disabled = st.session_state.current_question not in st.session_state.answered_questions
            st.button(next_label, key="next_btn", on_click=handle_next_question, disabled=next_disabled)
        
        # Add feedback section below the buttons
        if st.session_state.current_question in st.session_state.answered_questions:
            # Get correct answer keys (split by comma if multiple)
            correct_keys = str(question_row['Key']).split(',')
            correct_keys = [key.strip() for key in correct_keys]
            
            st.markdown("---")  # Add a separator
            
            # Display correct/incorrect feedback
            if has_multiple_answers:
                # Multiple correct answers
                user_selections = st.session_state.multi_select_answers.get(st.session_state.current_question, [])
                
                # Map selected options back to keys
                option_to_key = {}
                for key in ['A', 'B', 'C', 'D', 'E']:
                    option_col = f'Option {key}'
                    if option_col in question_row and pd.notna(question_row[option_col]):
                        option_to_key[question_row[option_col]] = key
                
                user_selection_keys = []
                for selection in user_selections:
                    key = option_to_key.get(selection)
                    if key:
                        user_selection_keys.append(key)
                
                # Sort both lists for comparison
                user_selection_keys.sort()
                sorted_correct_keys = sorted(correct_keys)
                
                is_correct = user_selection_keys == sorted_correct_keys
                
                # Get correct answer text
                correct_answers_text = []
                for key in correct_keys:
                    if f'Option {key}' in question_row and pd.notna(question_row[f'Option {key}']):
                        option_text = question_row[f'Option {key}']
                        correct_answers_text.append(f"{key}) {option_text}")
                
                correct_display = ", ".join(correct_answers_text)
                
                if is_correct:
                    st.success(f"✓ Correct! The answers are: {correct_display}")
                else:
                    st.error(f"✗ Incorrect. The correct answers are: {correct_display}")
            else:
                # Single correct answer
                user_answer = st.session_state.get(f"q{st.session_state.current_question}")
                correct_key = correct_keys[0]
                
                # Check if the correct option column exists
                option_col = f'Option {correct_key}'
                if option_col in question_row and pd.notna(question_row[option_col]):
                    correct_option = question_row[option_col]
                    
                    is_correct = user_answer == correct_option
                    
                    if is_correct:
                        st.success(f"✓ Correct! The answer is: {correct_key}) {correct_option}")
                    else:
                        st.error(f"✗ Incorrect. The correct answer is: {correct_key}) {correct_option}")
            
            # Show explanation section
            st.subheader("Explanation:")
            
            # Check for Feedback column first
            if 'Feedback' in question_row and pd.notna(question_row['Feedback']):
                st.write(question_row['Feedback'])
            # Then check for Explanation as fallback
            elif 'Explanation' in question_row and pd.notna(question_row['Explanation']):
                st.write(question_row['Explanation'])
            else:
                st.write("No explanation provided for this question.")
                
            # Check for feedback/answer images
            # Try different naming patterns for answer images
            answer_image_path = get_question_image_path(st.session_state.selected_test, f"{question_num}_answer")
            if not answer_image_path:
                answer_image_path = get_question_image_path(st.session_state.selected_test, f"Answer{question_num}")
            if not answer_image_path:
                answer_image_path = get_question_image_path(st.session_state.selected_test, f"Picture{question_num}")
            
            if answer_image_path:
                img_b64 = get_image_as_base64(answer_image_path)
                if img_b64:
                    st.image(img_b64, caption="Explanation Image")

# RESULTS PAGE
elif st.session_state.page == "results":
    data = load_data()
    test_data = data[st.session_state.selected_test]
    
    st.title("Quiz Results")
    
    # Use the stored total time instead of recalculating
    if st.session_state.total_quiz_time is None:
        # If somehow we got here without setting the total time, calculate it
        st.session_state.total_quiz_time = time.time() - st.session_state.start_time
    
    total_time = st.session_state.total_quiz_time
    
    # Display results
    st.success(f"Your score: {st.session_state.score}/{len(test_data)} ({int(st.session_state.score/len(test_data)*100)}%)")
    st.info(f"Total time: {format_time(total_time)}")
    
    # Calculate average time per question
    avg_time = total_time / len(test_data)
    st.info(f"Average time per question: {format_time(avg_time)}")
    
    # Restart button
    st.button("Restart Quiz", key="restart_btn", on_click=handle_restart_quiz) 