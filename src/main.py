import streamlit as st
from streamlit_option_menu import option_menu
from page.conversation_result import show_conversation_result
from page.conversation_calls import show_conversation_call
from utils.logo import get_logo

with st.sidebar:
    st.sidebar.markdown(get_logo(), unsafe_allow_html=True)
    selected_main = option_menu(
        "Jobcenter",
        ["Zylinc", "Betjeninger"],
        icons=["headset", "gear"],
        menu_icon="bi-headset",
        default_index=0,
    )

    if selected_main == "Zylinc":
        selected_zylinc = option_menu(
            "Zylinc",
            ['Varighed af samtale', 'Resultat af opkald', 'Ventetid pr opkald', 'Antal af samtaler'],
            icons=['clock', 'check-circle', 'hourglass-split', 'telephone'],
            menu_icon="headset",
            default_index=0,
        )
    elif selected_main == "Betjeninger":
        selected_betjeninger = option_menu(
            "Betjeninger",
            ['Kø', 'Ansatte', 'Ressourcestyring'],
            icons=['list-task', 'people', 'tools'],
            menu_icon="gear",
            default_index=0,
        )

if selected_main == "Zylinc":
    if selected_zylinc == 'Varighed af samtale':
        st.write("## Varighed af samtale")
    elif selected_zylinc == 'Resultat af opkald':
        show_conversation_result()
    elif selected_zylinc == 'Ventetid pr opkald':
        st.write("## Ventetid pr opkald")
    elif selected_zylinc == 'Antal af samtaler':
        show_conversation_call()

elif selected_main == "Betjeninger":
    if selected_betjeninger == 'Kø':
        st.write("## Kø")
    elif selected_betjeninger == 'Ansatte':
        st.write("## Ansatte")
    elif selected_betjeninger == 'Ressourcestyring':
        st.write("## Ressourcestyring")
