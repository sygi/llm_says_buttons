import streamlit as st

def handle_buttons(options_list, round):
  columns = st.columns(len(options_list))
  option_chosen = None
  for option_id, (column, option) in enumerate(zip(columns, options_list)):
    with column:
      button_type = 'secondary'
      if len(st.session_state.answers_list) > round and option == st.session_state.answers_list[round]:
        button_type = 'primary'
      if st.button(option, use_container_width=True, type=button_type, key=f"button_{round}_{option_id}"):
        if len(st.session_state.answers_list) <= round:
          # this is happening on click
          option_chosen = option
          st.session_state.answers_list.append(option)
          st.rerun()  # need to refresh to disable the buttons

  if option_chosen is not None:
    # TODO: is this broken?
    st.write(f"User chose option: {option_chosen}")

def handle_slider(slider_info, round):
  slider_col, accept_col = st.columns([8, 1.5])
  with slider_col:
    disabled = len(st.session_state.answers_list) > round
    value = st.slider(
      label=slider_info["label"],
      key=f"slider{round}",
      min_value=slider_info["min"], max_value=slider_info["max"], value=slider_info["value"],
      step=slider_info["step"], disabled=disabled
    )

  with accept_col:
    if st.button("Accept", key=f"slider{round}_button", use_container_width=True):
      if len(st.session_state.answers_list) <= round:
        st.session_state.answers_list.append(str(value))
        st.rerun()  # need to refresh to disable the slider

def handle_date_picker(date_picker_info, round):
  key = f"date_picker{round}"
  def on_change():
    value = st.session_state[key]
    if len(st.session_state.answers_list) <= round:
      st.session_state.answers_list.append(str(value))

  disabled = len(st.session_state.answers_list) > round
  st.date_input(
    label=date_picker_info["label"],
    key=key, min_value=date_picker_info["min"], max_value=date_picker_info["max"],
    on_change=on_change, disabled=disabled
  )

def handle_text_input(text_input_info, round):
  key = f"text_input{round}"
  def on_change():
    value = st.session_state[key]
    if len(st.session_state.answers_list) <= round:
      st.session_state.answers_list.append(value)

  disabled = len(st.session_state.answers_list) > round
  label = text_input_info.get("label", "")
  label_visibility = "visible" if label else "collapsed"

  st.text_input(
    label=label, label_visibility=label_visibility,
    key=key, on_change=on_change, disabled=disabled
  )
