import streamlit as st
from streamlit_float import *

float_init(theme=True, include_unstable_primary=False)

def chat_content():
    st.session_state['contents'].append(st.session_state.content)

if 'contents' not in st.session_state:
    st.session_state['contents'] = []
    border = False
else:
    border = True

col1, col2 = st.columns([1,2])
with col1:
    with st.container(border=True):
        st.write('Hello streamlit')

with col2:
    with st.container(border=border):
        with st.container():
            st.chat_input(key='content', on_submit=chat_content) 
            button_b_pos = "0rem"
            button_css = float_css_helper(width="2.2rem", bottom=button_b_pos, transition=0)
            float_parent(css=button_css)
        if content:=st.session_state.content:
            with st.chat_message(name='robot'):
                for c in st.session_state.contents:
                    st.write(c)