import streamlit as st
from utils.logo import get_logo
from streamlit_option_menu import option_menu
from page.conversation_result import show_conversation_result
from page.conversation_calls import show_conversation_call

st.set_page_config(page_title="Jobcenter", page_icon="assets/favicon.ico", layout="wide")

with st.sidebar:
    st.sidebar.markdown(get_logo(), unsafe_allow_html=True)
    selected = option_menu(
        "Jobcenter",
        ['Varighed af samtale', 'Resultat af opkald', 'Ventetid pr opkald', 'Antal af samtaler'],
        icons=['bi-broadcast', 'bi-clock', 'bi-check-circle', 'bi-hourglass-split', 'bi-telephone'],
        menu_icon="bi-headset",
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#f0f0f0"},
            "icon": {"color": "#4a4a4a", "font-size": "18px"},
            "nav-link": {"font-size": "18px", "text-align": "left", "margin": "0px", "--hover-color": "#e0e0e0"},
            "nav-link-selected": {"background-color": "#d0d0d0", "color": "#4a4a4a"},
            "menu-title": {"font-size": "20px", "font-weight": "bold", "color": "#4a4a4a", "margin-bottom": "10px"},
        }
    )

if selected == 'Varighed af samtale':
    st.write("## Varighed af samtale")
elif selected == 'Antal af samtaler':
    show_conversation_call()
elif selected == 'Resultat af opkald':
    show_conversation_result()
elif selected == 'Ventetid pr opkald':
    st.write("## Ventetid pr opkald")
