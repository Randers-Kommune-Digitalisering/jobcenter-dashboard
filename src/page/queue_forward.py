import streamlit as st
import streamlit_antd_components as sac
import altair as alt
import pandas as pd
from utils.zylinc_data import load_queue_forward_data


def show_queue_forward():
    data = load_queue_forward_data()
    if data is None or "LastQueueDisplayName" not in data.columns:
        st.error("Ingen data tilgængelig.")
        return

    all_queues = sorted(data["FirstQueueDisplayName"].dropna().unique())
    selected_queue = st.selectbox("Vælg en kø (afsender)", all_queues)

    forwarded = data[
        (data["FirstQueueDisplayName"] == selected_queue) &
        data["LastQueueDisplayName"].notnull() &
        (data["LastQueueDisplayName"] != selected_queue)
    ].copy()

    forwarded["Result"] = forwarded["Result"].replace({
        "Answered": "Besvaret",
        "Missed": "Ikke besvaret"
    })

    if "StartTimeDenmark" in forwarded.columns:
        forwarded["StartTimeDenmark"] = pd.to_datetime(forwarded["StartTimeDenmark"])
    elif "StartTimeUtc" in forwarded.columns:
        forwarded["StartTimeDenmark"] = pd.to_datetime(forwarded["StartTimeUtc"])

    if forwarded.empty:
        st.info("Ingen viderestillede opkald fundet for denne kø.")
        return

    col_1 = st.columns([1])[0]
    with col_1:
        content_tabs = sac.tabs([
            sac.TabsItem('Dag', tag='Dag', icon='calendar-day'),
            sac.TabsItem('Uge', tag='Uge', icon='calendar-week'),
            sac.TabsItem('Måned', tag='Måned', icon='calendar-month'),
        ], color='dark', size='md', position='top', align='start', use_container_width=True)

    if content_tabs == 'Dag':
        unique_dates = sorted(forwarded['StartTimeDenmark'].dt.date.unique())
        if len(unique_dates) == 0:
            st.error("Ingen data tilgængelig for den valgte kø.")
            st.stop()

        selected_date = st.date_input(
            "Vælg en dato",
            value=max(unique_dates),
            min_value=min(unique_dates),
            max_value=max(unique_dates),
            key='queue_forward_date_input'
        )

        day_data = forwarded[forwarded['StartTimeDenmark'].dt.date == selected_date]

        grouped = day_data.groupby(["LastQueueDisplayName", "Result"]).size().reset_index(name="Antal opkald")
        st.header(f"Viderestillede opkald pr. modtager ({selected_date})", divider="gray")

        chart = alt.Chart(grouped).mark_bar().encode(
            y=alt.Y("LastQueueDisplayName:N", title="Modtager"),
            x=alt.X("Antal opkald:Q", title="Antal opkald"),
            color=alt.Color("Result:N", title="Resultat"),
            tooltip=[
                alt.Tooltip("LastQueueDisplayName:N", title="Modtager"),
                alt.Tooltip("Antal opkald:Q", title="Antal opkald"),
                alt.Tooltip("Result:N", title="Resultat"),
            ]
        ).properties(width=900, height=500)
        st.altair_chart(chart, use_container_width=True)

    if content_tabs == 'Uge':
        forwarded["Year"] = forwarded["StartTimeDenmark"].dt.year
        forwarded["Week"] = forwarded["StartTimeDenmark"].dt.isocalendar().week
        unique_years = sorted(forwarded["Year"].unique())
        selected_year = st.selectbox("Vælg år", unique_years, index=len(unique_years) - 1, key="queue_forward_year_week")
        unique_weeks = sorted(forwarded[forwarded["Year"] == selected_year]["Week"].unique())
        selected_week = st.selectbox("Vælg uge", unique_weeks, index=len(unique_weeks) - 1, key="queue_forward_week")

        week_data = forwarded[(forwarded["Year"] == selected_year) & (forwarded["Week"] == selected_week)]

        grouped = week_data.groupby(["LastQueueDisplayName", "Result"]).size().reset_index(name="Antal opkald")
        st.header(f"Viderestillede opkald pr. modtager (Uge {selected_week}, {selected_year})", divider="gray")

        chart = alt.Chart(grouped).mark_bar().encode(
            y=alt.Y("LastQueueDisplayName:N", title="Modtager"),
            x=alt.X("Antal opkald:Q", title="Antal opkald"),
            color=alt.Color("Result:N", title="Resultat"),
            tooltip=[
                alt.Tooltip("LastQueueDisplayName:N", title="Modtager"),
                alt.Tooltip("Antal opkald:Q", title="Antal opkald"),
                alt.Tooltip("Result:N", title="Resultat"),
            ]
        ).properties(width=900, height=500)
        st.altair_chart(chart, use_container_width=True)

    if content_tabs == 'Måned':
        forwarded["Year"] = forwarded["StartTimeDenmark"].dt.year
        forwarded["Month"] = forwarded["StartTimeDenmark"].dt.month
        unique_years = sorted(forwarded["Year"].unique())
        selected_year = st.selectbox("Vælg år", unique_years, index=len(unique_years) - 1, key="queue_forward_year_month")
        unique_months = sorted(forwarded[forwarded["Year"] == selected_year]["Month"].unique())
        month_names = {1: "Januar", 2: "Februar", 3: "Marts", 4: "April", 5: "Maj", 6: "Juni", 7: "Juli", 8: "August", 9: "September", 10: "Oktober", 11: "November", 12: "December"}
        month_options = [(m, month_names[m]) for m in unique_months]
        selected_month = st.selectbox("Vælg måned", month_options, format_func=lambda x: x[1], index=len(month_options) - 1, key="queue_forward_month")

        month_data = forwarded[(forwarded["Year"] == selected_year) & (forwarded["Month"] == selected_month[0])]

        grouped = month_data.groupby(["LastQueueDisplayName", "Result"]).size().reset_index(name="Antal opkald")
        st.header(f"Viderestillede opkald pr. modtager ({selected_month[1]} {selected_year})", divider="gray")

        chart = alt.Chart(grouped).mark_bar().encode(
            y=alt.Y("LastQueueDisplayName:N", title="Modtager"),
            x=alt.X("Antal opkald:Q", title="Antal opkald"),
            color=alt.Color("Result:N", title="Resultat"),
            tooltip=[
                alt.Tooltip("LastQueueDisplayName:N", title="Modtager"),
                alt.Tooltip("Antal opkald:Q", title="Antal opkald"),
                alt.Tooltip("Result:N", title="Resultat"),
            ]
        ).properties(width=900, height=500)
        st.altair_chart(chart, use_container_width=True)
