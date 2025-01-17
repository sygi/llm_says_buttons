# Based on the work of Jakub Sygnowski, Sherry Bai, and Lamone Armstrong
# done in Recurse Center.

import google.generativeai as genai
import os
import streamlit as st
import json
import conversation
import widgets

# TODOs:
# - more interaction methods
# - calculate the cost of the LLMs
# - actually kill billing if it goes above $5
# - serve things

TITLE = "LLM says buttons"
MAX_NUMBER_QUESTIONS = 4
st.set_page_config(page_title=TITLE)
st.title(TITLE)

def set_up_api_key():
  my_api_key = os.getenv('GEMINI_API_KEY')
  note_on_api_key = (
    "By default, we use our API key with a limited quota, shared among users. "
    "You can get your own key [here](https://aistudio.google.com/app/apikey). We "
    "only use your API key in your session and won't store it for the future"
  )
  api_key = st.text_input(label="optional API key", type="password", help=note_on_api_key) or my_api_key
  genai.configure(api_key=api_key)

set_up_api_key()
interface_llm, answer_llm = conversation.set_up_llms()

def clear():
    for key in st.session_state.keys():
        del st.session_state[key]

def initialize_field(field_name, value=None):
    if field_name not in st.session_state:
        st.session_state[field_name] = value

initialize_field("clarifying_questions_list", [])
initialize_field("answers_list", [])
initialize_field("options_list", [])
initialize_field("ready_to_answer", False)
initialize_field("answer", "")
initialize_field("answer_ready", False)

q_col, clear_col = st.columns([0.9, 0.1])
with q_col:
  question = st.text_input(
    "Your question",
    "What are some nearby restaurants? I am in Brooklyn.",
    on_change=clear)
with clear_col:
  st.write("")
  if st.button("Clear"):
      clear()
      st.rerun()

for round in range(MAX_NUMBER_QUESTIONS):
    if round > len(st.session_state.answers_list):
        continue

    # display all clarifying questins and their answers
    if len(st.session_state.clarifying_questions_list) == round:
        clarifying_question = conversation.get_clarifying_question(
            question,
            st.session_state.clarifying_questions_list,
            st.session_state.answers_list
        )
        if "CLEAR" in clarifying_question:
          st.session_state.ready_to_answer = True
          print("clear, breaking")
          break
        st.session_state.clarifying_questions_list.append(clarifying_question)
    else:
        clarifying_question = st.session_state.clarifying_questions_list[round]
    st.write(clarifying_question)

    if len(st.session_state.options_list) <= round:
        widget_info = conversation.get_options(question, clarifying_question)
        st.session_state.options_list.append(widget_info)
    else:
        widget_info = st.session_state.options_list[round]

    if widget_info["widget"] == "buttons":
        widgets.handle_buttons(widget_info["options"], round)
    elif widget_info["widget"] == "slider":
        widgets.handle_slider(widget_info, round)


# given clarifying questions and answers, get gemini to produce a final response
st.session_state.ready_to_answer |= len(st.session_state.answers_list) == MAX_NUMBER_QUESTIONS

# st.session_state.clarifying_questions_list
# st.session_state.answers_list
if st.session_state.ready_to_answer and not st.session_state.answer_ready:
    response = conversation.get_answer(
      question, st.session_state.clarifying_questions_list, st.session_state.answers_list
    )
    def data_generator():
        for chunk in response:
            a = chunk.text.replace("$", "\\$")
            st.session_state.answer += a
            yield a
        st.session_state.answer_ready = True
    st.write_stream(data_generator)

elif st.session_state.answer_ready:
    st.write(st.session_state.answer)
