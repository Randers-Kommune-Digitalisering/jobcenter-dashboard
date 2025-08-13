import streamlit as st
from streamlit_option_menu import option_menu
from page.conversation_result import show_conversation_result
from page.conversation_calls import show_conversation_call
from page.conversation_queue_time import show_queue_time
from page.operations import show_operations
from utils.logo import get_logo
from page.live import display_live_data
from page.conversation_duration import show_conversation_duration
from page.conversation_activity import show_conversation_activity
from page.queue_forward import show_queue_forward

st.set_page_config(page_title="Jobcenter", page_icon="assets/favicon.ico", layout="wide")

with st.sidebar:
    st.sidebar.markdown(get_logo(), unsafe_allow_html=True)
    selected_main = option_menu(
        "Jobcenter",
        ["Zylinc", "FrontDesk"],
        icons=["headset", "gear"],
        menu_icon="bi bi-briefcase-fill",
        default_index=0,
    )

    if selected_main == "Zylinc":
        selected_zylinc = option_menu(
            "Zylinc",
            ['Live Data', 'Varighed af samtale', 'Resultat af opkald', 'Ventetid pr opkald', 'Antal af samtaler', 'Opkaldsaktivitet', 'Viderestilling af opkald'],
            icons=['broadcast', 'bi bi-clock-history', 'bi bi-check2-square', 'hourglass-split', 'bi bi-telephone-outbound-fill', 'bi bi-telephone-minus-fill', 'bi bi-phone-flip'],
            menu_icon="headset",
            default_index=0,
        )
    elif selected_main == "FrontDesk":
        selected_betjeninger = option_menu(
            "FrontDesk",
            ['Betjeninger', 'Ansatte'],
            icons=['list-task', 'people', 'tools'],
            menu_icon="gear",
            default_index=0,
        )

if selected_main == "Zylinc":
    if selected_zylinc == 'Live Data':
        display_live_data()
    elif selected_zylinc == 'Varighed af samtale':
        show_conversation_duration()
    elif selected_zylinc == 'Resultat af opkald':
        show_conversation_result()
    elif selected_zylinc == 'Ventetid pr opkald':
        show_queue_time()
    elif selected_zylinc == 'Antal af samtaler':
        show_conversation_call()
    elif selected_zylinc == 'Opkaldsaktivitet':
        show_conversation_activity()
    elif selected_zylinc == 'Viderestilling af opkald':
        show_queue_forward()


elif selected_main == "FrontDesk":
    if selected_betjeninger == 'Betjeninger':
        st.write("## Betjeninger")
        show_operations()
    elif selected_betjeninger == 'Ansatte':
        st.write("## Ansatte")
