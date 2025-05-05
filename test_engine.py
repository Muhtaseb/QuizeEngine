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
if 'multi_select_answers' not in st.session_state:
    st.session_state.multi_select_answers = {}

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
    st.session_state.current_question += 1
    
    # Reset show_answer for the next question
    if st.session_state.current_question not in st.session_state.show_answer:
        st.session_state.show_answer[st.session_state.current_question] = False
    
    # Check if we need to go to results page
    data = load_data()
    test_data = data[st.session_state.selected_test]
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
    st.session_state.multi_select_answers = {}

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
                if f'Option {key}' in question_row and pd.notna(question_row[f'Option {key}']):
                    option_to_key[question_row[f'Option {key}']] = key
            
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
    selected_options = st.session_state[f"multi_q{st.session_state.current_question}"]
    st.session_state.multi_select_answers[st.session_state.current_question] = selected_options

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
            selected = st.multiselect(
                "Choose all correct answers:", 
                options, 
                key=f"multi_q{st.session_state.current_question}",
                on_change=update_multi_select,
                default=st.session_state.multi_select_answers.get(st.session_state.current_question, [])
            )
        else:
            # For single answer, use radio button
            st.radio("Select your answer:", options, key=f"q{st.session_state.current_question}")
        
        # Show answer button and feedback
        answer_col, feedback_col = st.columns([1, 3])
        with answer_col:
            st.button("Show Answer", key=f"answer_btn_{st.session_state.current_question}", 
                     on_click=handle_show_answer)
            
        with feedback_col:
            # Check if we should show the answer
            if st.session_state.current_question in st.session_state.answered_questions:
                # Get correct answer keys (split by comma if multiple)
                correct_keys = str(question_row['Key']).split(',')
                correct_keys = [key.strip() for key in correct_keys]
                
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
                
                # Show feedback/explanation section with better formatting
                st.markdown("---")
                st.subheader("Explanation:")
                
                # Check for Feedback column first
                if 'Feedback' in question_row and pd.notna(question_row['Feedback']):
                    st.write(question_row['Feedback'])
                # Then check for Explanation as fallback
                elif 'Explanation' in question_row and pd.notna(question_row['Explanation']):
                    st.write(question_row['Explanation'])
                else:
                    st.write("No explanation provided for this question.")
        
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