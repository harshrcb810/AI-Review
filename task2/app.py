import streamlit as st
import json
import os
from datetime import datetime
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')
DATA_FILE = "feedback_data.json"
ADMIN_PASSWORD = "123456"

def init_data_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)

# Load feedback data
def load_feedback():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# Save feedback data
def save_feedback(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Generate AI response for user 
def generate_user_response(rating, review):
    prompt = f"""You are a friendly and empathetic customer service AI. A customer has submitted feedback with a {rating}-star rating.

Customer Review: "{review}"

Based on the rating and review:
- If 4-5 stars: Thank them warmly, acknowledge specific positives they mentioned, and encourage continued engagement
- If 3 stars: Thank them, acknowledge their concerns, and express commitment to improvement
- If 1-2 stars: Apologize sincerely, acknowledge their frustration, assure them their feedback is valuable, and express commitment to resolve issues

Generate a personalized, empathetic response (2-3 sentences) that addresses their specific feedback."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Thank you for your feedback! We value your input and will use it to improve our services."

# Generate AI summary for admin 
def generate_admin_summary(rating, review):
    prompt = f"""Analyze this customer feedback and provide a concise summary (1-2 sentences) highlighting the key points and sentiment.

Rating: {rating}/5 stars
Review: "{review}"

Focus on: main issues/praises, sentiment tone, and urgency level."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "Analysis unavailable."

# Generate recommended actions for admin 
def generate_recommended_actions(rating, review):
    prompt = f"""Based on this customer feedback, suggest 2-3 specific, actionable recommendations for the business.

Rating: {rating}/5 stars
Review: "{review}"

Provide concrete actions such as:
- If low rating (1-2): Immediate follow-up, issue investigation, compensation consideration
- If medium rating (3): Process improvement, training needs, service enhancement
- If high rating (4-5): Leverage positive feedback, request testimonial, maintain standards

Format as a bulleted list with specific, actionable items."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "• Review feedback\n• Take appropriate action\n• Follow up with customer"

# User Dashboard
def user_dashboard():
    st.title("Customer Feedback")
    st.markdown("### We value your opinion!")
    
    with st.form("feedback_form"):
        rating = st.select_slider(
            "⭐ Rate your experience",
            options=[1, 2, 3, 4, 5],
            value=5
        )
        
        st.markdown(f"**Selected Rating: {'⭐' * rating}**")
        
        review = st.text_area(
            "📄 Share your experience",
            placeholder="Tell us about your experience...",
            height=150
        )
        
        submitted = st.form_submit_button("Submit Feedback", use_container_width=True)
        
        if submitted:
            if review.strip():
                with st.spinner("Processing your feedback..."):
                    ai_response = generate_user_response(rating, review)
                    admin_summary = generate_admin_summary(rating, review)
                    recommended_actions = generate_recommended_actions(rating, review)
                    
                    # Create feedback entry
                    feedback_entry = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "rating": rating,
                        "review": review,
                        "ai_response": ai_response,
                        "admin_summary": admin_summary,
                        "recommended_actions": recommended_actions
                    }
                    
                    
                    feedback_data = load_feedback()
                    feedback_data.append(feedback_entry)
                    save_feedback(feedback_data)
                    
                    st.success("Thank you for your feedback!")
                    st.markdown("---")
                    st.markdown("### Response:")
                    st.info(ai_response)
                    
            else:
                st.error("Please write a review before submitting.")
# Admin Dashboard
def admin_dashboard():
    st.title("Admin Dashboard")
    
    # Password protection
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        password = st.text_input("Enter Admin Password", type="password")
        if st.button("Login"):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        st.stop()
    
    # Load feedback data
    feedback_data = load_feedback()
    
    if not feedback_data:
        st.info("No feedback submissions yet.")
        return
    
    # Logout button
    if st.button("Logout"):
        st.session_state.admin_authenticated = False
        st.rerun()
    
    # Analytics Section
    st.markdown("## Analytics Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Feedback", len(feedback_data))
    
    with col2:
        avg_rating = sum([f['rating'] for f in feedback_data]) / len(feedback_data)
        st.metric("Average Rating", f"{avg_rating:.2f} ⭐")
    
    with col3:
        positive_count = sum([1 for f in feedback_data if f['rating'] >= 4])
        st.metric("Positive Reviews", f"{positive_count} ({positive_count/len(feedback_data)*100:.0f}%)")
    
    with col4:
        negative_count = sum([1 for f in feedback_data if f['rating'] <= 2])
        st.metric("Needs Attention", f"{negative_count} ({negative_count/len(feedback_data)*100:.0f}%)")
    
    # Visualizations
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Rating Distribution
        rating_counts = Counter([f['rating'] for f in feedback_data])
        fig_ratings = go.Figure(data=[
            go.Bar(
                x=list(range(1, 6)),
                y=[rating_counts.get(i, 0) for i in range(1, 6)],
                marker_color=['#e74c3c', '#e67e22', '#f39c12', '#2ecc71', '#27ae60'],
                text=[rating_counts.get(i, 0) for i in range(1, 6)],
                textposition='auto',
            )
        ])
        fig_ratings.update_layout(
            title="Rating Distribution",
            xaxis_title="Star Rating",
            yaxis_title="Count",
            showlegend=False,
            height=300
        )
        st.plotly_chart(fig_ratings, use_container_width=True)
    
    with col_chart2:
        # Ratings Over Time
        df = pd.DataFrame(feedback_data)
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_avg = df.groupby('date')['rating'].mean().reset_index()
        
        fig_trend = go.Figure(data=[
            go.Scatter(
                x=daily_avg['date'],
                y=daily_avg['rating'],
                mode='lines+markers',
                marker=dict(size=10, color='#3498db'),
                line=dict(width=3, color='#3498db')
            )
        ])
        fig_trend.update_layout(
            title="Average Rating Trend",
            xaxis_title="Date",
            yaxis_title="Average Rating",
            yaxis_range=[0, 5],
            height=300
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # Sentiment Distribution
    sentiment_data = {
        'Positive (4-5★)': sum([1 for f in feedback_data if f['rating'] >= 4]),
        'Neutral (3★)': sum([1 for f in feedback_data if f['rating'] == 3]),
        'Negative (1-2★)': sum([1 for f in feedback_data if f['rating'] <= 2])
    }
    
    fig_sentiment = go.Figure(data=[
        go.Pie(
            labels=list(sentiment_data.keys()),
            values=list(sentiment_data.values()),
            marker_colors=['#27ae60', '#f39c12', '#e74c3c'],
            hole=0.4
        )
    ])
    fig_sentiment.update_layout(
        title="Sentiment Distribution",
        height=300
    )
    st.plotly_chart(fig_sentiment, use_container_width=True)
    
    # Feedback List
    st.markdown("---")
    st.markdown("## All Feedback Submissions")
    
    # Filter options
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        filter_rating = st.multiselect(
            "Filter by Rating",
            options=[1, 2, 3, 4, 5],
            default=[1, 2, 3, 4, 5]
        )
    
    with col_filter2:
        sort_order = st.selectbox(
            "Sort by",
            options=["Most Recent", "Highest Rating", "Lowest Rating"]
        )
    
    # Apply filters
    filtered_data = [f for f in feedback_data if f['rating'] in filter_rating]
    
    # Apply sorting
    if sort_order == "Most Recent":
        filtered_data = sorted(filtered_data, key=lambda x: x['timestamp'], reverse=True)
    elif sort_order == "Highest Rating":
        filtered_data = sorted(filtered_data, key=lambda x: x['rating'], reverse=True)
    else:
        filtered_data = sorted(filtered_data, key=lambda x: x['rating'])
    
    # Display feedback cards
    for idx, feedback in enumerate(filtered_data):
        with st.expander(f"{'⭐' * feedback['rating']} - {feedback['timestamp']} - ID: {feedback['id'][-6:]}"):
            col_info1, col_info2 = st.columns([1, 3])
            
            with col_info1:
                st.markdown(f"**Rating:**")
                st.markdown(f"# {'⭐' * feedback['rating']}")
                st.markdown(f"**Timestamp:**")
                st.text(feedback['timestamp'])
            
            with col_info2:
                st.markdown("**Customer Review:**")
                st.info(feedback['review'])
                
                st.markdown("**AI Summary:**")
                st.success(feedback['admin_summary'])
                
                st.markdown("**Recommended Actions:**")
                st.warning(feedback['recommended_actions'])
                
                st.markdown("**User Response Sent:**")
                st.text(feedback['ai_response'])

# Main App
def main():
    st.set_page_config(
        page_title="AI Feedback System",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize data file
    init_data_file()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Dashboard",
        ["User Feedback", "Admin Dashboard"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Stats")
    feedback_data = load_feedback()
    st.sidebar.metric("Total Submissions", len(feedback_data))
    if feedback_data:
        avg_rating = sum([f['rating'] for f in feedback_data]) / len(feedback_data)
        st.sidebar.metric("Average Rating", f"{avg_rating:.2f} ⭐")
    
    st.sidebar.markdown("---")
    st.sidebar.info("** ** Admin password is `123456`\n")
    
    if page == "User Feedback":
        user_dashboard()
    else:
        admin_dashboard()

if __name__ == "__main__":
    main()