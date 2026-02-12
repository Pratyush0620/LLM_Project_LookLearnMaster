"""
Quick Learn - Adaptive Assessment Platform
Main Streamlit Application

An LLM-powered adaptive assessment system that generates questions from PDFs,
adjusts difficulty based on performance, and generates detailed reports.
"""

import streamlit as st
from datetime import datetime
from pdf_extractor import extract_text_from_pdf, get_content_summary
from llm_handler import AdaptiveLLM
from report_generator import generate_assessment_report, get_weak_topics


# Page Configuration
st.set_page_config(
    page_title="Quick Learn - Adaptive Assessment",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful UI
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        color: #a0aec0;
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Card styling */
    .card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    /* Question card */
    .question-card {
        background: linear-gradient(145deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid rgba(102, 126, 234, 0.3);
        margin: 1rem 0;
    }
    
    /* Difficulty badges */
    .difficulty-easy {
        background: linear-gradient(90deg, #48bb78 0%, #38a169 100%);
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .difficulty-medium {
        background: linear-gradient(90deg, #ed8936 0%, #dd6b20 100%);
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .difficulty-hard {
        background: linear-gradient(90deg, #f56565 0%, #e53e3e 100%);
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Stats cards */
    .stat-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stat-label {
        color: #a0aec0;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* Radio button styling */
    .stRadio > div {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 15px;
        padding: 1rem;
    }
    
    .stRadio > div > label {
        color: #e2e8f0 !important;
        font-size: 1rem;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        transition: all 0.2s ease;
    }
    
    .stRadio > div > label:hover {
        background: rgba(102, 126, 234, 0.2);
    }
    
    /* Success/Error messages */
    .success-message {
        background: linear-gradient(90deg, rgba(72, 187, 120, 0.2) 0%, rgba(56, 161, 105, 0.2) 100%);
        border: 1px solid #48bb78;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .error-message {
        background: linear-gradient(90deg, rgba(245, 101, 101, 0.2) 0%, rgba(229, 62, 62, 0.2) 100%);
        border: 1px solid #f56565;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(26, 26, 46, 0.95);
    }
    
    /* File uploader */
    .stFileUploader {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 1rem;
        border: 2px dashed rgba(102, 126, 234, 0.5);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'pdf_content': None,
        'pdf_name': None,
        'api_key': None,
        'llm': None,
        'current_question': None,
        'questions_history': [],
        'current_difficulty': 1,
        'performance_window': [],  # Last N answers for adaptive difficulty
        'assessment_started': False,
        'assessment_complete': False,
        'total_questions': 0,
        'correct_answers': 0,
        'asked_questions': [],
        'show_feedback': False,
        'last_feedback': None,
        'max_difficulty_reached': 1,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def calculate_adaptive_difficulty(performance_window: list, current_difficulty: int) -> int:
    """
    Calculate new difficulty based on recent performance.
    
    Rules:
    - If 2+ correct in last 3: increase difficulty
    - If 2+ incorrect in last 3: decrease difficulty
    - Otherwise: maintain current difficulty
    """
    if len(performance_window) < 3:
        return current_difficulty
    
    recent = performance_window[-3:]
    correct_count = sum(recent)
    
    if correct_count >= 2 and current_difficulty < 3:
        return current_difficulty + 1
    elif correct_count <= 1 and current_difficulty > 1:
        return current_difficulty - 1
    
    return current_difficulty


def get_performance_metrics() -> dict:
    """Calculate current performance metrics."""
    total = st.session_state.total_questions
    correct = st.session_state.correct_answers
    
    if total == 0:
        accuracy = 0
        avg_difficulty = 1
    else:
        accuracy = (correct / total) * 100
        difficulties = [q.get('difficulty', 1) for q in st.session_state.questions_history]
        avg_difficulty = sum(difficulties) / len(difficulties) if difficulties else 1
    
    return {
        'total_questions': total,
        'correct_answers': correct,
        'accuracy': accuracy,
        'avg_difficulty': avg_difficulty,
        'max_difficulty_reached': st.session_state.max_difficulty_reached,
        'current_difficulty': st.session_state.current_difficulty
    }


def render_sidebar():
    """Render the sidebar with API key and PDF upload."""
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "🔑 Cohere API Key",
            type="password",
            value=st.session_state.api_key or "",
            help="Enter your Cohere API key to use Command R+",
            placeholder="Enter your Cohere API key here"
        )
        
        if api_key and api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            st.session_state.llm = AdaptiveLLM(api_key)
            st.success("✅ API Key set!")
        
        st.markdown("---")
        
        # PDF Upload
        st.markdown("## 📄 Upload Learning Material")
        uploaded_file = st.file_uploader(
            "Upload a PDF file",
            type=['pdf'],
            help="Upload the PDF document you want to be assessed on"
        )
        
        if uploaded_file:
            if uploaded_file.name != st.session_state.pdf_name:
                try:
                    with st.spinner("📖 Extracting content..."):
                        content = extract_text_from_pdf(uploaded_file)
                        st.session_state.pdf_content = content
                        st.session_state.pdf_name = uploaded_file.name
                        # Reset assessment on new PDF
                        st.session_state.assessment_started = False
                        st.session_state.assessment_complete = False
                        st.session_state.questions_history = []
                        st.session_state.total_questions = 0
                        st.session_state.correct_answers = 0
                        st.session_state.current_difficulty = 1
                        st.session_state.performance_window = []
                        st.session_state.asked_questions = []
                        st.session_state.max_difficulty_reached = 1
                    
                    st.success(f"✅ Loaded: {uploaded_file.name}")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        if st.session_state.pdf_content:
            st.markdown("---")
            with st.expander("📝 Content Preview"):
                preview = get_content_summary(st.session_state.pdf_content, 500)
                st.text(preview)
        
        st.markdown("---")
        
        # Stats in sidebar
        if st.session_state.assessment_started:
            st.markdown("## 📊 Live Stats")
            metrics = get_performance_metrics()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Questions", metrics['total_questions'])
                st.metric("Correct", metrics['correct_answers'])
            with col2:
                st.metric("Accuracy", f"{metrics['accuracy']:.0f}%")
                diff_names = {1: "Easy", 2: "Medium", 3: "Hard"}
                st.metric("Level", diff_names[metrics['current_difficulty']])


def render_welcome():
    """Render the welcome screen."""
    st.markdown('<h1 class="main-header">📚 Quick Learn</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Adaptive Assessment Platform</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card">
            <h3>🎯 Adaptive Learning</h3>
            <p style="color: #a0aec0;">
                Questions automatically adjust to your skill level. 
                Perform well? Get harder questions. 
                Struggling? We'll help you build up.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <h3>📄 PDF-Based</h3>
            <p style="color: #a0aec0;">
                Upload any learning material as PDF. 
                Our AI generates relevant questions 
                directly from your content.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card">
            <h3>📊 Detailed Reports</h3>
            <p style="color: #a0aec0;">
                Get comprehensive PDF reports with 
                performance analysis and personalized 
                improvement suggestions.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Check if ready to start
    if not st.session_state.api_key:
        st.warning("⚠️ Please enter your Cohere API key in the sidebar to get started.")
    elif not st.session_state.pdf_content:
        st.info("📄 Upload a PDF document in the sidebar to begin your assessment.")
    else:
        st.success("✅ You're all set! Click below to start your adaptive assessment.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Assessment", use_container_width=True):
                st.session_state.assessment_started = True
                st.rerun()


def render_question():
    """Render the current question."""
    # Generate new question if needed
    if st.session_state.current_question is None or st.session_state.show_feedback == False:
        if not st.session_state.show_feedback:
            with st.spinner("🤔 Generating question..."):
                question_data = st.session_state.llm.generate_question(
                    content=st.session_state.pdf_content,
                    difficulty=st.session_state.current_difficulty,
                    asked_questions=st.session_state.asked_questions
                )
                st.session_state.current_question = question_data
                st.session_state.asked_questions.append(question_data.get('question', ''))
    
    question = st.session_state.current_question
    
    # Header with stats
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = get_performance_metrics()
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{metrics['total_questions']}</div>
            <div class="stat-label">Questions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{metrics['accuracy']:.0f}%</div>
            <div class="stat-label">Accuracy</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        diff_names = {1: "Easy", 2: "Medium", 3: "Hard"}
        diff_colors = {1: "difficulty-easy", 2: "difficulty-medium", 3: "difficulty-hard"}
        st.markdown(f"""
        <div class="stat-card">
            <span class="{diff_colors[st.session_state.current_difficulty]}">{diff_names[st.session_state.current_difficulty]}</span>
            <div class="stat-label" style="margin-top: 0.75rem;">Current Level</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{diff_names[metrics['max_difficulty_reached']]}</div>
            <div class="stat-label">Max Level</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Question display
    if question.get('error'):
        st.error(f"Error: {question.get('error_message', 'Unknown error')}")
        st.warning(f"Question text: {question.get('question', 'No details')}")
        if st.button("🔄 Try Again"):
            st.session_state.current_question = None
            st.rerun()
        return
    
    st.markdown(f"""
    <div class="question-card fade-in">
        <span class="{diff_colors[question.get('difficulty', 1)]}" style="margin-bottom: 1rem; display: inline-block;">
            {diff_names[question.get('difficulty', 1)]} • {question.get('topic', 'General')}
        </span>
        <h3 style="color: #e2e8f0; margin-top: 1rem; line-height: 1.6;">
            {question.get('question', 'Question not available')}
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Answer options
    if not st.session_state.show_feedback:
        options = question.get('options', {})
        
        answer = st.radio(
            "Select your answer:",
            options=list(options.keys()),
            format_func=lambda x: f"{x}. {options.get(x, '')}",
            key=f"answer_{st.session_state.total_questions}"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✅ Submit Answer", use_container_width=True):
                # Evaluate answer
                feedback = st.session_state.llm.evaluate_answer(
                    question=question.get('question', ''),
                    user_answer=answer,
                    correct_answer=question.get('correct_answer', ''),
                    options=options,
                    content=st.session_state.pdf_content
                )
                
                is_correct = feedback['is_correct']
                
                # Update stats
                st.session_state.total_questions += 1
                if is_correct:
                    st.session_state.correct_answers += 1
                
                # Update performance window
                st.session_state.performance_window.append(1 if is_correct else 0)
                
                # Calculate new difficulty
                new_difficulty = calculate_adaptive_difficulty(
                    st.session_state.performance_window,
                    st.session_state.current_difficulty
                )
                
                # Track max difficulty
                if new_difficulty > st.session_state.max_difficulty_reached:
                    st.session_state.max_difficulty_reached = new_difficulty
                
                # Store in history
                st.session_state.questions_history.append({
                    'question': question.get('question', ''),
                    'topic': question.get('topic', 'General'),
                    'difficulty': question.get('difficulty', 1),
                    'user_answer': answer,
                    'correct_answer': question.get('correct_answer', ''),
                    'is_correct': is_correct,
                    'explanation': question.get('explanation', '')
                })
                
                # Prepare difficulty change message
                if new_difficulty > st.session_state.current_difficulty:
                    feedback['difficulty_change'] = "📈 Great job! Difficulty increased!"
                elif new_difficulty < st.session_state.current_difficulty:
                    feedback['difficulty_change'] = "📉 Don't worry! Adjusting difficulty to help you learn."
                else:
                    feedback['difficulty_change'] = None
                
                st.session_state.current_difficulty = new_difficulty
                st.session_state.last_feedback = feedback
                st.session_state.show_feedback = True
                st.rerun()
    
    else:
        # Show feedback
        feedback = st.session_state.last_feedback
        
        if feedback['is_correct']:
            st.markdown(f"""
            <div class="success-message fade-in">
                <h3 style="color: #48bb78; margin-bottom: 0.5rem;">✅ Correct!</h3>
                <p style="color: #9ae6b4;">{feedback.get('feedback', 'Well done!')}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="error-message fade-in">
                <h3 style="color: #fc8181; margin-bottom: 0.5rem;">❌ Not quite right</h3>
                <p style="color: #feb2b2;">{feedback.get('feedback', 'Keep trying!')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show correct answer
            correct = question.get('correct_answer', '')
            options = question.get('options', {})
            st.info(f"**Correct Answer:** {correct}. {options.get(correct, '')}\n\n**Explanation:** {question.get('explanation', '')}")
        
        # Show difficulty change
        if feedback.get('difficulty_change'):
            st.success(feedback['difficulty_change'])
        
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col2:
            if st.button("➡️ Next Question", use_container_width=True):
                st.session_state.current_question = None
                st.session_state.show_feedback = False
                st.session_state.last_feedback = None
                st.rerun()
        
        with col3:
            if st.button("🏁 Finish Assessment", use_container_width=True):
                st.session_state.assessment_complete = True
                st.rerun()


def render_results():
    """Render the final results and report generation."""
    st.markdown('<h1 class="main-header">🎉 Assessment Complete!</h1>', unsafe_allow_html=True)
    
    metrics = get_performance_metrics()
    
    # Performance summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{metrics['total_questions']}</div>
            <div class="stat-label">Total Questions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{metrics['correct_answers']}</div>
            <div class="stat-label">Correct Answers</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{metrics['accuracy']:.1f}%</div>
            <div class="stat-label">Accuracy</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        diff_names = {1: "Easy", 2: "Medium", 3: "Hard"}
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{diff_names[metrics['max_difficulty_reached']]}</div>
            <div class="stat-label">Max Difficulty</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Performance grade
    if metrics['accuracy'] >= 90:
        grade = "🌟 Excellent"
        grade_msg = "Outstanding performance! You've mastered this material."
    elif metrics['accuracy'] >= 75:
        grade = "👍 Good"
        grade_msg = "Great job! You have a solid understanding of the content."
    elif metrics['accuracy'] >= 60:
        grade = "📈 Satisfactory"
        grade_msg = "Good effort! With some review, you'll improve quickly."
    else:
        grade = "📚 Needs Improvement"
        grade_msg = "Keep practicing! Review the suggested topics below."
    
    st.markdown(f"""
    <div class="card" style="text-align: center;">
        <h2 style="color: #667eea;">{grade}</h2>
        <p style="color: #a0aec0; font-size: 1.1rem;">{grade_msg}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Weak topics
    weak_topics = get_weak_topics(st.session_state.questions_history)
    
    if weak_topics:
        st.markdown("### ⚠️ Topics to Review")
        for topic in weak_topics:
            st.markdown(f"- {topic}")
    
    st.markdown("---")
    
    # Generate and download report
    st.markdown("### 📥 Download Your Report")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("📄 Generate PDF Report", use_container_width=True):
            with st.spinner("Generating your personalized report..."):
                # Get improvement suggestions from LLM
                suggestions = st.session_state.llm.generate_improvement_suggestions(
                    performance_data=metrics,
                    weak_topics=weak_topics,
                    content=st.session_state.pdf_content
                )
                
                # Generate PDF
                pdf_bytes = generate_assessment_report(
                    performance_data=metrics,
                    questions_history=st.session_state.questions_history,
                    improvement_suggestions=suggestions,
                    content_title=f"Assessment: {st.session_state.pdf_name}"
                )
                
                # Download button
                st.download_button(
                    label="⬇️ Download Report",
                    data=pdf_bytes,
                    file_name=f"assessment_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.success("✅ Report generated! Click above to download.")
    
    st.markdown("---")
    
    # Restart option
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Start New Assessment", use_container_width=True):
            # Reset state
            st.session_state.assessment_started = False
            st.session_state.assessment_complete = False
            st.session_state.questions_history = []
            st.session_state.total_questions = 0
            st.session_state.correct_answers = 0
            st.session_state.current_difficulty = 1
            st.session_state.performance_window = []
            st.session_state.current_question = None
            st.session_state.asked_questions = []
            st.session_state.max_difficulty_reached = 1
            st.session_state.show_feedback = False
            st.session_state.last_feedback = None
            st.rerun()


def main():
    """Main application entry point."""
    init_session_state()
    render_sidebar()
    
    if st.session_state.assessment_complete:
        render_results()
    elif st.session_state.assessment_started:
        render_question()
    else:
        render_welcome()


if __name__ == "__main__":
    main()
