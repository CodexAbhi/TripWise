import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import re

# Loading environment variables
load_dotenv()

# Get API key from .env file
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

class SmartTravelAssistant:
    def __init__(self):
        # Initialize Groq
        self.client = Groq(api_key=GROQ_API_KEY)
        
        # Define initial information gathering fields 
        self.INFORMATION_FIELDS = [
            {
                "key": "current_location", 
                "prompt": "Starting Location", 
                "description": "Where are you beginning your journey?",
                "placeholder": "Enter your current city or region"
            },
            {
                "key": "destination", 
                "prompt": "Travel Destination", 
                "description": "What's your dream destination?",
                "placeholder": "Enter your desired destination"
            },
            {
                "key": "travel_dates", 
                "prompt": "Travel Dates", 
                "description": "When do you plan to start your trip?",
                "placeholder": "Select approximate dates"
            },
            {
                "key": "trip_duration", 
                "prompt": "Trip Duration", 
                "description": "How long will you be traveling?",
                "placeholder": "e.g., 5 days, 1 week"
            },
            {
                "key": "budget", 
                "prompt": "Budget Range", 
                "description": "What's your budget for this trip?",
                "placeholder": "Estimated total budget in local currency"
            },
            {
                "key": "travelers", 
                "prompt": "Travel Companions", 
                "description": "How many people are traveling?",
                "placeholder": "Number of travelers including yourself"
            }
        ]

    def query_ai(self, prompt, context=None, max_tokens=1024):
        """Send query to AI and get response"""
        try:
            messages = [
                {"role": "system", "content": "You are an expert in concise, helpful travel planning."},
                {"role": "user", "content": prompt}
            ]
            
            if context:
                messages.insert(1, {"role": "user", "content": f"Context: {context}"})
            
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            st.error(f"AI Query Error: {e}")
            return "I'm having trouble processing that right now."

    def generate_location_review(self, location):
        """Generate a quick AI-powered review of the location"""
        prompt = f"Provide a 2-line travel insight about {location}, focusing on its seasonal characteristics, unique attractions, or travel experience."
        return self.query_ai(prompt)

    def validate_information(self, collected_info):
        """Validate collected information and suggest follow-up questions"""
        prompt = f"""
        Generate 3-4 specific follow-up questions about the travel details.
        Only return the questions, no additional text.
        
        Travel Information:
        {collected_info}
        """
        
        validation_result = self.query_ai(prompt)
        return validation_result

    def generate_itinerary(self, collected_info):
        """Generate detailed travel itinerary"""
        prompt = f"""
        Create a comprehensive, personalized travel itinerary based on:
        {collected_info}

        Guidelines:
        - Be practical and detailed
        - Include day-by-day suggestions
        - Consider budget and companions
        - Highlight unique local experiences
        - Provide flexible options
        """
        
        itinerary = self.query_ai(prompt, max_tokens=2048)
        return itinerary

    def render_travel_assistant(self):
        # Custom CSS
        st.markdown("""
        <style>
        .stApp {
            background-color: #1a1a1a;
        }
        .main-title {
            color: #2c3e50;
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 20px;
        }
        .section-title {
            color: #34495e;
            font-size: 1.5rem;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .input-description {
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-bottom: 5px;
        }
        .stTextInput > div > div > input {
            background-color: #1a1a1a;
            border-radius: 5px;
            padding: 10px;
        }
        .stButton > button {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
        }
        .location-review {
            background-color: #419FC8;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
        }
        </style>
        """, unsafe_allow_html=True)

        # Initialize session state
        if 'travel_state' not in st.session_state:
            st.session_state.travel_state = {
                'collected_info': {},
                'current_field_index': 0,
                'inputs': {},
                'stage': 'gathering_initial',
                'follow_up_data': []
            }

        # Main app layout
        st.markdown('<h1 class="main-title">🌍 Smart Travel Companion</h1>', unsafe_allow_html=True)

        # Main logic based on current stage
        if st.session_state.travel_state['stage'] == 'gathering_initial':
            self._gather_initial_information()
        
        elif st.session_state.travel_state['stage'] == 'follow_up_questions':
            self._handle_follow_up_questions()
        
        elif st.session_state.travel_state['stage'] == 'generate_itinerary':
            self._generate_final_itinerary()

    def _gather_initial_information(self):
        current_fields = self.INFORMATION_FIELDS

        # Render all input fields at once
        for field in current_fields:
            st.markdown(f'<h3 class="section-title">{field["prompt"]}</h3>', unsafe_allow_html=True)
            
            user_input = st.text_input(
                label=field["description"],
                placeholder=field["placeholder"],
                key=f"input_{field['key']}",
                value=st.session_state.travel_state['inputs'].get(field['key'], '')
            )

            # Special handling for destination to show location review
            if field['key'] == 'destination' and user_input:
                review = self.generate_location_review(user_input)
                st.markdown(f'<div class="location-review">{review}</div>', unsafe_allow_html=True)

            # Preserve input in session state
            st.session_state.travel_state['inputs'][field['key']] = user_input
            st.session_state.travel_state['collected_info'][field['key']] = user_input

        # Add a single submit button at the end
        if st.button("Continue to Follow-up Questions", key="initial_submit"):
            # Validate that all fields have been filled
            if all(st.session_state.travel_state['inputs'].values()):
                st.session_state.travel_state['stage'] = 'follow_up_questions'
                # Trigger a page refresh
                st.rerun()
            else:
                st.warning("Please fill out all fields before continuing.")

    def _handle_follow_up_questions(self):
        # Generate follow-up questions only once
        if not st.session_state.travel_state['follow_up_data']:
            info_summary = "\n".join([f"{k}: {v}" for k, v in st.session_state.travel_state['collected_info'].items()])
            validation_result = self.validate_information(info_summary)
            
            # Clean and split questions
            follow_up_matches = [q.strip() for q in validation_result.split('\n') if q.strip() and '?' in q]
            
            # Store follow-up questions
            st.session_state.travel_state['follow_up_data'] = follow_up_matches

        st.markdown('<h2 class="main-title">Follow-up Questions</h2>', unsafe_allow_html=True)

        # Render follow-up questions
        all_answered = True
        for i, question in enumerate(st.session_state.travel_state['follow_up_data'], 1):
            user_answer = st.text_input(
                label=question, 
                value=st.session_state.travel_state['inputs'].get(f'follow_up_{i}', ''),
                key=f"follow_up_{i}",
                placeholder="Your detailed response"
            )
            
            # Preserve input in session state
            st.session_state.travel_state['inputs'][f'follow_up_{i}'] = user_answer
            
            if user_answer:
                st.session_state.travel_state['collected_info'][f'follow_up_{i}'] = user_answer
            else:
                all_answered = False

        # Generate Itinerary button+
        if st.button("Generate My Travel Itinerary", disabled=not all_answered):
            if all_answered:
                st.session_state.travel_state['stage'] = 'generate_itinerary'
                st.rerun()
            else:
                st.warning("Please answer all follow-up questions.")

    def _generate_final_itinerary(self):
        st.markdown('<h2 class="main-title">🗺️ Your Personalized Travel Plan</h2>', unsafe_allow_html=True)
        
        with st.spinner('Crafting your personalized journey...'):
            # Combine all collected information
            info_summary = "\n".join([f"{k}: {v}" for k, v in st.session_state.travel_state['collected_info'].items()])
            
            itinerary = self.generate_itinerary(info_summary)
        
        # Display itinerary with enhanced styling
        st.markdown(f"""
        <div style="background-color: #419FC8; border-radius: 10px; padding: 20px; margin-top: 20px;">
        <h3 style="color: #2c3e50;">Itinerary Overview</h3>
        <p style="white-space: pre-wrap;">{itinerary}</p>
        </div>
        """, unsafe_allow_html=True)

        # Reset button with improved styling
        if st.button("Plan Another Trip", key="reset_button"):
            st.session_state.travel_state = {
                'collected_info': {},
                'current_field_index': 0,
                'inputs': {},
                'stage': 'gathering_initial',
                'follow_up_data': []
            }
            st.rerun()

def main():
    travel_assistant = SmartTravelAssistant()
    travel_assistant.render_travel_assistant()

if __name__ == "__main__":
    main()