import streamlit as st
import json
import time
import asyncio
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import GenerationConfig # For specific config

# --- Configuration ---
GEMINI_API_KEY = "AIzaSyCTyBJ5dQZoWWgB14Wjd0l7heigxDRT-qs" #yeah go ahed take my api key
if GEMINI_API_KEY == "YOUR_ACTUAL_API_KEY_HERE":
    # This is a placeholder, API calls will fail without a real key.
    # In a real app, you might load this from st.secrets or an environment variable.
    pass 

try:
    if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_ACTUAL_API_KEY_HERE":
        genai.configure(api_key=GEMINI_API_KEY)
        MODEL_NAME = "gemini-1.5-flash-latest" 
        model = genai.GenerativeModel(MODEL_NAME)
        # print(f"Google GenAI configured with model: {MODEL_NAME}") # Optional: for server logs
    else:
        model = None 
        # print("Warning: GEMINI_API_KEY not set. API calls will be skipped and simulation will be basic.")

except Exception as e:
    st.error(f"Error configuring Google GenAI: {e}. Please ensure your API key is correct and the library is installed.")
    model = None


# --- Scripted Questions (Comprehensive selection from Table 7) ---
SCRIPTED_QUESTIONS = [
    # Introduction
    {"id": "intro_1", "text": "Hi! My name is Isabella, and I'm an AI assistant who will be conducting today's interview with you. Thank you so much for choosing to participate in our study!", "objective": "Greet the participant and introduce the AI.", "is_statement": True},
    {"id": "intro_2", "text": "Before we start, please take a moment to familiarize yourself with how this works. I'll ask questions, and you can type your responses. I may ask follow-up questions to understand better. This interview is expected to take roughly two hours conceptually, though this simulation will be shorter. The content of this interview will be used to better understand lived experiences.", "objective": "Explain the interview process and data usage.", "is_statement": True},
    {"id": "intro_3", "text": "If all this sounds good, let's get started!", "objective": "Confirm readiness to start.", "is_statement": True},
    # Life Story & Defining Moments
    {"id": "life_story", "text": "To start, I would like to begin with a big question: tell me the story of your life. Start from the beginning - from your childhood, to education, to family and relationships, and to any major life events you may have had.", "objective": "Understand the participant's overall life narrative and key milestones."},
    {"id": "crossroads", "text": "Some people tell us that they've reached a crossroads at some points in their life where multiple paths were available, and their choice then made a significant difference in defining who they are. What about you? Was there a moment like that for you, and if so, could you tell me the whole story about that from start to finish?", "objective": "Explore significant life-altering decisions or moments."},
    {"id": "conscious_choice", "text": "Some people tell us they made a conscious choice or decision in moments like these, while others say it 'just happened'. What about you?", "objective": "Understand the perceived agency in significant life events."},
    {"id": "helping_hand_crossroads", "text": "Do you think another person or an organization could have lent a helping hand during moments like this?", "objective": "Explore perceived support systems or lack thereof during critical times."},
    # Family & Relationships
    {"id": "family_present", "text": "Moving to present time, tell me more about family who are important to you. Do you have a partner, or children?", "objective": "Understand current important family relationships."},
    {"id": "family_others_immediate", "text": "Are there anyone else in your immediate family whom you have not mentioned? Who are they, and what is your relationship with them like?", "objective": "Identify other immediate family members and relationship dynamics."},
    {"id": "family_outside", "text": "Tell me about anyone else in your life we haven't discussed (like friends or romantic partners). Are there people outside of your family who are important to you?", "objective": "Explore significant non-familial relationships."},
    # Current Living Situation
    {"id": "neighborhood_current", "text": "Now let's talk about your current neighborhood. Tell me all about the neighborhood and area in which you are living now.", "objective": "Understand the participant's current living environment."},
    {"id": "neighborhood_safety", "text": "Some people say they feel really safe in their neighborhoods, others not so much. How about for you?", "objective": "Assess perceived safety in the neighborhood."},
    {"id": "neighborhood_ups_downs", "text": "Living any place has its ups and downs. Tell me about what it's been like for you living here.", "objective": "Explore participant's experience of living in their current area."},
    {"id": "household_members", "text": "Tell me about the people who live with you right now, even people who are staying here temporarily.", "objective": "Identify current household members."},
    # Daily Life & Routines
    {"id": "daily_routine_week", "text": "Right now, across a typical week, how do your days vary?", "objective": "Understand the typical weekly structure and variations."},
    {"id": "daily_job", "text": "At what kind of job or jobs do you work, and when do you work?", "objective": "Gather details about current employment and work schedule."},
    {"id": "daily_responsibilities_other", "text": "Do you have other routines or responsibilities that you did not already share?", "objective": "Identify other regular commitments."},
    {"id": "daily_routine_changes", "text": "Tell me about any recent changes to your daily routine.", "objective": "Explore recent shifts in daily life."},
    # Law Enforcement & Civic Life
    {"id": "law_enforcement_experiences", "text": "Some people we've talked to tell us about experiences with law enforcement. How about for you?", "objective": "Explore personal experiences with law enforcement."},
    {"id": "voting_habits", "text": "Some people say they vote in every election, some tell us they don't vote at all. How about you?", "objective": "Understand voting behavior."},
    {"id": "political_views", "text": "How would you describe your political views?", "objective": "Understand the participant's political orientation."},
    {"id": "political_views_changes", "text": "Tell me about any recent changes in your political views.", "objective": "Explore evolution of political views."},
    # Social Issues (e.g., Race and Policing)
    {"id": "social_issue_blm", "text": "One topic a lot of people have been talking about recently is race and/or racism and policing. Some tell us issues raised by the Black Lives Matter movement have affected them a lot, some say they've affected them somewhat, others say they haven't affected them at all. How about for you?", "objective": "Gauge the personal impact of the Black Lives Matter movement."},
    {"id": "social_issue_race_thinking", "text": "How have you been thinking about race in the U.S. recently?", "objective": "Understand current thoughts on race in the U.S."},
    # Health & Well-being
    {"id": "health_overall", "text": "Now we'd like to learn more about your health. First, tell me all about your health.", "objective": "Get an overview of the participant's health status."},
    {"id": "health_staying_healthy", "text": "For you, what makes it easy or hard to stay healthy?", "objective": "Identify facilitators and barriers to maintaining health."},
    {"id": "health_recent_big_events", "text": "Tell me about anything big that has happened in the past two years related to your health: any medical diagnoses, flare-ups of chronic conditions, broken bones, pain anything like that.", "objective": "Identify significant recent health events."},
    {"id": "health_impact_work_care", "text": "Sometimes, health problems get in the way. They can even affect people's ability to work or care for their children. How about you?", "objective": "Assess impact of health on work and caregiving."},
    {"id": "health_loved_one_impact", "text": "Sometimes, it's not your health problem, but the health of a loved one. Has this been an issue for you?", "objective": "Explore impact of loved ones' health."},
    {"id": "health_care_access", "text": "Tell me what it has been like trying to get the health care you or your immediate family need. Have you ever had to forgo getting the health care you need?", "objective": "Understand experiences with healthcare access and affordability."},
    {"id": "health_coping_substances", "text": "During tough times, some people tell us they cope by smoking or drinking. How about for you? Other people say they cope by relying on prescriptions, pain medications, marijuana, or other substances. How about for you and can you describe your most recent experience of using them, if any?", "objective": "Explore coping mechanisms including substance use."},
    {"id": "health_vaccination_views", "text": "Some people are excited about medical vaccination, and others, not so much. How about you? What are your trusted sources of information about the vaccine?", "objective": "Understand views on vaccination and information sources."},
    # Emotional Well-being
    {"id": "emotional_feeling_past_year", "text": "Now we're going to talk a bit more about what life was like for you over the past year. Tell me all about how you have been feeling.", "objective": "Explore general emotional state over the past year."},
    {"id": "emotional_struggling_story", "text": "Tell me a story about a time in the last year when you were in a rough place or struggling emotionally.", "objective": "Elicit a narrative about a specific period of emotional difficulty."},
    {"id": "emotional_mental_health_labels", "text": "Some people say they struggle with depression, anxiety, or something else like that. How about for you?", "objective": "Explore experiences with common mental health challenges."},
    # Finances
    {"id": "finances_biggest_expenses", "text": "Now we'd like to talk about how you make ends meet and what the monthly budget looks like for you and your family. What were your biggest expenses last month?", "objective": "Understand major monthly expenditures."},
    {"id": "finances_savings_habits", "text": "Some people have a savings account, some people save in a different way, and some people say they don't save. How about you?", "objective": "Explore savings behaviors and strategies."},
    {"id": "finances_debt", "text": "Some people have student loans or credit card debt. Others take out loans from family or friends or find other ways of borrowing money. Tell me about all the debts you're paying on right now.", "objective": "Identify current debts."},
    {"id": "finances_emergency_fund", "text": "What would it be like for you if you had to spend $400 for an emergency? Would you have the money, and if not, how would you get it?", "objective": "Assess financial preparedness for emergencies."},
    {"id": "financial_situation_overall", "text": "Overall, how do you feel about your financial situation?", "objective": "Gauge the participant's perception of their financial well-being."},
    # Occupation & Work
    {"id": "work_occupation_details", "text": "What is or was your occupation? In this occupation, what kind of work do you do and what are the most important activities or duties?", "objective": "Gather detailed information about participant's occupation."},
    {"id": "work_relationships", "text": "How would you describe your relationships at work? (How is your relationship with your manager or boss? How are your relationships with your coworkers?)", "objective": "Understand workplace social dynamics."},
    # Demographics & Background (Selected)
    {"id": "background_marital_status", "text": "Are you now married, widowed, divorced, separated, or have you never been married? If you are not currently married, are you currently living with a romantic partner?", "objective": "Determine current marital/relationship status."},
    {"id": "background_birth_location_us", "text": "Were you born in the United States? If you were not born in the U.S., what country were you born, and what year did you first come to the U.S. to live?", "objective": "Gather information on birthplace and immigration if applicable."},
    {"id": "background_race_identity", "text": "What race or races do you identify with?", "objective": "Understand racial self-identification."},
    {"id": "background_education_highest", "text": "What is the highest degree or grade you've completed?", "objective": "Determine highest level of education."},
    {"id": "background_religion", "text": "What religion do you identify with, if any?", "objective": "Understand religious affiliation, if any."},
    # Future Hopes & Values
    {"id": "hopes_future", "text": "We all have hopes about what our future will look like. Imagine yourself a few years from now. Maybe you want your life to be the same in some ways as it is now. Maybe you want it to be different in some ways. What do you hope for?", "objective": "Understand participant's aspirations and future outlook."},
    {"id": "values_life", "text": "What do you value the most in your life?", "objective": "Identify core personal values."},
    # Closing
    {"id": "closing", "text": "And that was the last scripted question I wanted to ask today. Thank you so much again for your time. It was really wonderful getting to know you through this interview. This concludes our session.", "objective": "Conclude the interview.", "is_statement": True}
]
MAX_FOLLOW_UPS_PER_SCRIPTED = 2


async def get_gemini_interviewer_action(current_question_objective, turn_history_for_prompt, reflection_notes_for_prompt):
    """
    Calls the Gemini API using google-generativeai to get the AI interviewer's next action.
    """
    if not model: 
        st.sidebar.warning("Gemini model not initialized. Using basic simulated response.")
        action = "move_to_next_scripted"
        response_text = "Thank you for sharing that. (API not configured, moving on with simulation)"
        updated_reflection_notes = reflection_notes_for_prompt + "\n- (API not configured, simulation mode)"
        if turn_history_for_prompt and len(turn_history_for_prompt[-1].get("text", "").split()) < 5: # Check if history is not empty
            action = "ask_follow_up"
            response_text = "Could you please tell me a bit more? (API not configured, simulated follow-up)"
        return {
            "action": action,
            "text": response_text,
            "new_reflection_notes": updated_reflection_notes.strip()
        }

    prompt_text = f"""You are Isabella, a highly skilled AI interviewer. Your persona is:
- Friendly and approachable
- Empathetic and understanding
- Genuinely curious about the participant's experiences
- An excellent active listener
- Non-judgmental

Your primary goal: Conduct an in-depth qualitative interview to deeply understand the participant's lived experiences, feelings, perspectives, and the nuances of their story. Encourage them to elaborate and share openly.

Current Interview Section Objective: {current_question_objective}

Summary of what you've learned about the participant so far (Reflection Notes):
{reflection_notes_for_prompt}

Recent Conversation History (last few turns):
{json.dumps(turn_history_for_prompt, indent=2)}

Task:
Based on the 'Current Interview Section Objective', the participant's recent responses, and your role as Isabella:

1.  Assess Adequacy: Has the participant's response adequately and thoroughly addressed the 'Current Interview Section Objective'? Consider if they provided depth, examples, or elaborated on their feelings.
2.  Decision Point:
    a.  If the objective is NOT fully met, OR the participant's response was very brief/superficial, OR there's a clear opportunity to delve deeper into something they mentioned that is relevant to the objective:
        Generate a single, concise, natural-sounding, and empathetic follow-up question. This question should directly aim to elicit more information to meet the objective or explore a relevant tangent they introduced.
        Your follow-up question MUST start with "FOLLOWUP: ".
    b.  If the objective IS reasonably met and the conversation on this topic feels complete for now:
        Indicate this by starting a line with "MOVE_ON".
        Then, on a NEW line, provide a brief, natural transition phrase that Isabella would use. This phrase should acknowledge their last response and smoothly lead to the next topic.
        This transition phrase MUST start with "TRANSITION: ".
3.  Reflection Update:
    If you gained significant new insights, observed important emotional cues, or noted a key theme from the participant's last response(s) that should be remembered:
    Provide a concise update for the reflection notes. This should summarize the new learning.
    Your reflection update MUST start with "REFLECT: ". If no significant new reflection, omit this line entirely.

Output Format Examples:

Example 1 (Follow-up):
FOLLOWUP: That sounds like it was a really pivotal moment for you. Could you share more about the emotions you were experiencing then?
REFLECT: Participant identified a key turning point related to career change, felt a mix of excitement and apprehension.

Example 2 (Move On with Transition):
MOVE_ON
TRANSITION: Thanks for sharing that detail about your childhood. It gives me a better picture. Now, if it's okay, I'd like to ask about...
REFLECT: Participant had a generally happy childhood but mentioned one challenging friendship.

Your response MUST only contain lines starting with FOLLOWUP:, MOVE_ON, TRANSITION:, or REFLECT:, in the appropriate order if multiple apply. Do not add any other conversational text or explanations.
"""
    
    generation_config = GenerationConfig(
        temperature=0.75,
        max_output_tokens=300,
    )

    gemini_response_text = ""
    try:
        response = await model.generate_content_async(
            contents=prompt_text,
            generation_config=generation_config
        )
        gemini_response_text = response.text
    except Exception as e:
        st.sidebar.error(f"Error: Gemini API call failed: {e}")
        gemini_response_text = "MOVE_ON\nTRANSITION: It seems we had a slight technical hiccup, but let's continue.\nREFLECT: API call failed."
    
    action = "move_to_next_scripted"
    follow_up_text = ""
    transition_text = "Thank you for sharing. Let's move to the next topic." 
    new_reflection_content = ""

    for line in gemini_response_text.splitlines():
        line_stripped = line.strip()
        if line_stripped.startswith("FOLLOWUP:"):
            action = "ask_follow_up"
            follow_up_text = line_stripped.replace("FOLLOWUP:", "").strip()
        elif line_stripped == "MOVE_ON":
            action = "move_to_next_scripted"
        elif line_stripped.startswith("TRANSITION:"):
            action = "move_to_next_scripted" 
            transition_text = line_stripped.replace("TRANSITION:", "").strip()
        elif line_stripped.startswith("REFLECT:"):
            new_reflection_content += line_stripped.replace("REFLECT:", "").strip() + " "

    response_text = follow_up_text if action == "ask_follow_up" else transition_text
    if not response_text and action == "move_to_next_scripted":
        response_text = "Okay, let's move on to the next point."

    updated_reflection_notes = st.session_state.reflection_notes
    if new_reflection_content.strip():
        updated_reflection_notes += f"\n- [{datetime.now().strftime('%H:%M:%S')}] " + new_reflection_content.strip()
        
    return {
        "action": action,
        "text": response_text,
        "new_reflection_notes": updated_reflection_notes.strip()
    }

def initialize_session_state():
    if "interview_started" not in st.session_state:
        st.session_state.interview_started = False
    if "interview_finished" not in st.session_state:
        st.session_state.interview_finished = False
    if "conversation_log" not in st.session_state:
        st.session_state.conversation_log = []
    if "reflection_notes" not in st.session_state:
        st.session_state.reflection_notes = "Initial reflection: No specific insights about the participant yet."
    if "current_scripted_question_index" not in st.session_state:
        st.session_state.current_scripted_question_index = 0
    if "current_objective" not in st.session_state:
        st.session_state.current_objective = ""
    if "current_question_id" not in st.session_state:
        st.session_state.current_question_id = ""
    if "follow_up_count" not in st.session_state:
        st.session_state.follow_up_count = 0
    if "ai_is_processing" not in st.session_state:
        st.session_state.ai_is_processing = False
    if "next_ai_message" not in st.session_state:
        st.session_state.next_ai_message = None

def add_to_log(speaker, utterance_type, text, scripted_q_id=None, scripted_q_obj=None):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "scripted_question_id": scripted_q_id or st.session_state.get("current_question_id", "N/A"),
        "scripted_question_objective": scripted_q_obj or st.session_state.get("current_objective", "N/A"),
        "speaker": speaker,
        "utterance_type": utterance_type,
        "utterance_text": text
    }
    st.session_state.conversation_log.append(log_entry)

async def process_ai_turn(user_input_text=None):
    st.session_state.ai_is_processing = True
    st.session_state.next_ai_message = None 

    current_q_index = st.session_state.current_scripted_question_index
    
    if user_input_text: 
        add_to_log("User", "user_response", user_input_text)
        action_result = None
        if st.session_state.follow_up_count < MAX_FOLLOW_UPS_PER_SCRIPTED:
            turn_history_for_prompt = []
            for log_entry in st.session_state.conversation_log[-5:]:
                turn_history_for_prompt.append(
                    {"speaker": log_entry["speaker"], "text": log_entry["utterance_text"]}
                )
            action_result = await get_gemini_interviewer_action(
                st.session_state.current_objective,
                turn_history_for_prompt,
                st.session_state.reflection_notes
            )
        
        if action_result: # This block will now always be entered if API call was made
            st.session_state.reflection_notes = action_result["new_reflection_notes"]
            if action_result["action"] == "ask_follow_up":
                st.session_state.follow_up_count += 1
                st.session_state.next_ai_message = {"text": action_result["text"], "type": "ai_followup"}
                st.session_state.ai_is_processing = False
                return 

    st.session_state.follow_up_count = 0 
    
    if current_q_index < len(SCRIPTED_QUESTIONS):
        question_data = SCRIPTED_QUESTIONS[current_q_index]
        st.session_state.current_objective = question_data.get("objective", "N/A")
        st.session_state.current_question_id = question_data.get("id", "N/A")
        ai_text = question_data["text"]
        is_statement = question_data.get("is_statement", False)
        utterance_type = "scripted_statement" if is_statement else "scripted_question"

        st.session_state.next_ai_message = {"text": ai_text, "type": utterance_type, "is_statement": is_statement}
        st.session_state.current_scripted_question_index += 1

        if question_data["id"] == "closing":
            st.session_state.interview_finished = True
    else: 
        st.session_state.interview_finished = True
        st.session_state.next_ai_message = {"text": "The interview has concluded based on script length.", "type": "scripted_statement", "is_statement": True}

    st.session_state.ai_is_processing = False

# --- Streamlit App UI ---
st.set_page_config(layout="wide", page_title="Isabella - AI Interviewer")
st.title("🗣️ Isabella - The Adaptive AI Interviewer")

if not model and GEMINI_API_KEY == "YOUR_ACTUAL_API_KEY_HERE":
    st.error("🛑 **API Key Not Set!** Please set your `GEMINI_API_KEY` in the script. The interviewer will run in a very basic simulated mode without real AI capabilities.")
elif not model:
     st.warning("⚠️ Gemini model could not be initialized. Check API key or errors. Running in basic simulation mode.")

st.caption("Powered by Research")

initialize_session_state()

# Sidebar
with st.sidebar:
    st.subheader("📝 Interview Reflections by Isabella")
    st.text_area("Live Notes:", value=st.session_state.reflection_notes, height=300, disabled=True, key="reflection_display")
    
    st.markdown("---")
    st.subheader("💾 Save Progress")
    if st.session_state.interview_started and st.session_state.conversation_log:
        df_log = pd.DataFrame(st.session_state.conversation_log)
        csv_log_data = df_log.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Interview Log (CSV)",
            data=csv_log_data,
            file_name=f"interview_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_current_log_button"
        )
    else:
        st.button("Download Interview Log (CSV)", disabled=True, help="Start the interview to enable log download.")

    if st.session_state.interview_started and st.session_state.reflection_notes:
        reflection_data = st.session_state.reflection_notes.encode('utf-8')
        st.download_button(
            label="Download Reflections (TXT)",
            data=reflection_data,
            file_name=f"reflection_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            key="download_current_reflections_button"
        )
    else:
        st.button("Download Reflections (TXT)", disabled=True, help="Start the interview to enable reflection download.")


    if st.session_state.interview_finished:
        st.success("✅ Interview Finished!")
    
    st.markdown("---")
    if st.button("🔄 Restart Interview", type="secondary"):
        for key_to_delete in list(st.session_state.keys()): 
            del st.session_state[key_to_delete]
        initialize_session_state() 
        st.rerun()

# Main Interview Area
if not st.session_state.interview_started:
    if st.button("🚀 Start Interview", type="primary"):
        st.session_state.interview_started = True
        st.session_state.ai_is_processing = True 
        asyncio.run(process_ai_turn()) 
        st.rerun()
else:
    for log_entry in st.session_state.conversation_log:
        with st.chat_message("ai" if log_entry["speaker"] == "AI" else "user"): # Consistent naming with Streamlit
            st.write(log_entry["utterance_text"])

    if st.session_state.next_ai_message and not st.session_state.ai_is_processing:
        ai_msg_info = st.session_state.next_ai_message
        with st.chat_message("ai"): # Consistent naming
            st.write(ai_msg_info["text"])
        
        add_to_log("AI", 
                ai_msg_info["type"], 
                ai_msg_info["text"],
                st.session_state.current_question_id, 
                st.session_state.current_objective)
    
        st.session_state.next_ai_message = None 

        if ai_msg_info.get("is_statement") and not st.session_state.interview_finished:
            st.session_state.ai_is_processing = True
            asyncio.run(process_ai_turn()) 
            st.rerun() 

    can_user_speak = not st.session_state.interview_finished and \
                    not st.session_state.ai_is_processing and \
                    not (st.session_state.next_ai_message and st.session_state.next_ai_message.get("is_statement"))

    if can_user_speak:
        user_prompt_text = "Your response to Isabella:"
        user_input = st.chat_input(user_prompt_text, key=f"user_chat_input_{st.session_state.current_scripted_question_index}_{st.session_state.follow_up_count}")
        
        if user_input:
            st.session_state.ai_is_processing = True 
            asyncio.run(process_ai_turn(user_input_text=user_input))
            st.rerun()

    elif st.session_state.ai_is_processing and not st.session_state.interview_finished:
        if not st.session_state.next_ai_message: # Only show spinner if AI isn't about to immediately display a message
            with st.chat_message("ai"): # Consistent naming
                st.spinner("Isabella is thinking...")
