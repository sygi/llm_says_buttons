import json
from typing import Any
import os
import random
import re
import google.generativeai as genai

MAX_NUMBER_OPTIONS = 5

def set_up_llms():
  small_llm_list = ["gemini-1.5-flash-8b", "gemini-1.5-flash"]
  # "gemini-2.0-flash-exp" has a small tier 1 quota
  big_llm_list = ["gemini-1.5-pro"]
  model = genai.GenerativeModel(random.choice(small_llm_list))
  big_model = genai.GenerativeModel(random.choice(big_llm_list))
  return model, big_model

interface_llm, answer_llm = set_up_llms()

def _get_past_summary(past_questions: list[str], past_answers: list[str]) -> str:
  past_summary = ""
  for q, a in zip(past_questions, past_answers, strict=True):
    past_summary += f"- Q: '{q}' A: '{a}'\n"
  return past_summary

def get_clarifying_question(question: str, past_questions: list[str], past_answers: list[str]) -> str:
  template_first = (
      f"I work in support and received this question from a user: '{question}'. "
      "What is one question I can ask to clarify the request? "
      "Start by thinking step by step about the potential clarifications "
      "and the needs of the user, and then answer with: \n"
      "<question>your question</question>, eg. <question>What is your budget?</question>"
  )

  past_summary = _get_past_summary(past_questions, past_answers)
  template_following = (
    f"I work in support and received this question from a user: '{question}'. "
      "I already asked a number of clarifying questions to understand it better. Here are they with their answers:\n"
      + past_summary +
      "Is the question entirely well-defined now, or should I ask more questions to be able to fully answer without more questions? "
      "Make sure we have all the information necessary to give a comprehensive answer, tailored to the user. "
      "Start by thinking step by step about a potential clarification and needs of the user. \n"
      "If you think the question doesn't need any more clarifications, answer with: <question>CLEAR</question>.\n"
      "Other, answer with <question>your question</question>, eg. <question>What is your budget?</question>"
      "Respond only with a single, short clarification question, about a single aspect of the user's question."
      "Refer to the user as you (not as they)."
  )
  template = template_following if past_questions else template_first
  print(f"asking {template=}")
  answer = interface_llm.generate_content(template).text
  print(f"Got an answer of {answer=}")
  final_part = re.search(r"<question>(.+?)</question>", answer, re.DOTALL)
  print(f"{final_part=}")
  if final_part:
    answer = final_part.group(1)
  else:
    answer = "CLEAR"
  return answer

def get_options(question: str, clarifying_question: str) -> dict[str, Any]:
  follow_up = (
    "You are an UI designer tasked with creating an interface to clarify user questions."
    f"Here is a question I got from a user: '{question}'. I will ask a follow-up question '{clarifying_question}'"
    "to clarify their request. What type of interface should I use to get the answer from the user? "
    "First, choose a widget, out of: a list of buttons, a color picker, a numerical slider, a date picker, or a text input.\n"
    "The format of the answer will be JSON.\n"
    "1. For buttons, the format should be {\"widget\": \"buttons\", \"options\": [\"option1\", \"option2\", \"option3\"]}.\n"
    f"Use at most {MAX_NUMBER_OPTIONS} options: they should cover the popular answer. Each of them should be a single, concrete answer that a user could say."
    "2. For color picker, the format should be {\"widget\": \"color\"}.\n"
    "3. For the numerical slider, the format should be {\"widget\": \"slider\", \"label\": \"price\", \"min\": 0, \"max\": 100, \"step\": 1, \"value\": 50}.\n"
    "4. For date picker, the format should be {\"widget\": \"datepicker\", \"label\": \"price\", \"min\": \"2023-01-01\", \"max\": \"2023-12-31\"}.\n"
 #   "5. For text input, the format should be {\"widget\": \"text\", \"label\": \"Explanation\"}.\n"
    "Only choose out of these options: buttons, color, slider, datepicker, don't choose any other widget.\n"
    "First, think step by step, and add the JSON at the end of your answer. Follow the JSON format strictly, don't add any extra fields."
  )
  def drop_tickticktick(text):
    prefix = "```json"
    json_position = text.find(prefix)
    if json_position != -1:
        text = text[json_position + len(prefix):]
    print(f"{text=}")
    text = text.strip()
    if text.endswith("```"):
        text = text[:-len("```")]

    print(f"{text=}")
    return text

  response = interface_llm.generate_content(follow_up)
  print(f"got {response.text=}")
  options = drop_tickticktick(response.text)
  options_list = json.loads(options)
  if isinstance(options_list, list):
    options_list = options_list[0]
  if "options" in options_list:
    options_list["options"] = [k.replace("$", "\\$") for k in options_list["options"]][:MAX_NUMBER_OPTIONS]
  return options_list

def get_answer(question: str, clarifying_questions: list[str], answers: list[str]):
  past_context = _get_past_summary(clarifying_questions, answers)
  if past_context:
    past_context = (
    "I asked a number of clarifying questions, here are their answers:\n"
    + past_context +
    "Based on all this information, "
    )
  template = (
      f"I got this question from the user '{question}'. "
      + past_context +
      f"Can you provivide a final answer?"
  )
  print(f"asked {template=}")
  response = answer_llm.generate_content(template, stream=True)
  return response
