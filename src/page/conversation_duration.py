import streamlit as st
import streamlit_antd_components as sac
from datetime import datetime
import altair as alt
import pandas as pd
from utils.zylinc_data import load_and_process_data_from_zylinc_db, convert_minutes_to_hms, get_all_queues_with_tables


def show_conversation_duration():
    st.sidebar.header("Jobcenter Kø")
    queue_table_mapping = get_all_queues_with_tables()
    all_queues = list(queue_table_mapping.keys())

    selected_queue_display = st.sidebar.selectbox("Vælg en kø", all_queues, key='queue_select')
    original_queue_name, selected_table = queue_table_mapping[selected_queue_display]

    historical_data = load_and_process_data_from_zylinc_db(table_name=selected_table, queue_name=original_queue_name)
    if historical_data is None:
        st.error("Failed to fetch data from the database.")
        st.stop()

    col_1 = st.columns([1])[0]

    with col_1:
        content_tabs = sac.tabs([
            sac.TabsItem('Dag', tag='Dag'),
            sac.TabsItem('Uge', tag='Uge'),
            sac.TabsItem('Kvartal', tag='Kvartal'),
        ], color='dark', size='md', position='top', align='start', use_container_width=True)

    if content_tabs == 'Dag':
        unique_dates = historical_data['StartTimeDenmark'].dt.date.unique()

        if len(unique_dates) == 0:
            st.error("Ingen data tilgængelig for den valgte kø.")
            st.stop()

        if 'date_input' in st.session_state:
            if st.session_state['date_input'] < min(unique_dates) or st.session_state['date_input'] > max(unique_dates):
                st.session_state['date_input'] = max(unique_dates)

        selected_date = st.date_input(
            "Vælg en dato",
            value=st.session_state.get('date_input', max(unique_dates)),
            min_value=min(unique_dates),
            max_value=max(unique_dates),
            key='date_input'
        )

        historical_data_today = historical_data[
            (historical_data['StartTimeDenmark'].dt.date == selected_date) &
            (historical_data['StartTimeDenmark'].dt.time.between(
                datetime.strptime('05:00', '%H:%M').time(),
                datetime.strptime('18:00', '%H:%M').time()
            ))
        ]

        if historical_data_today.empty:
            st.error("Ingen data tilgængelig for den valgte dato.")
            st.stop()

        avg_duration_today = historical_data_today[historical_data_today['Result'] == 'Answered']['DurationMinutes'].mean()
        avg_duration_today = 0 if pd.isna(avg_duration_today) else avg_duration_today

        st.metric(label="Gennemsnitlig varighed af besvarede opkald(Dag)", value=convert_minutes_to_hms(avg_duration_today))

        historical_data_today['TimeInterval'] = historical_data_today['StartTimeDenmark'].dt.floor('30T')
        chart_data = historical_data_today.groupby(['TimeInterval', 'AgentDisplayName']).agg({'DurationMinutes': 'mean'}).reset_index()

        st.write(f"## Varighed af samtale(Dag) - {selected_date}")
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('TimeInterval:T', title='Tidspunkt', axis=alt.Axis(format='%H:%M')),
            y=alt.Y('DurationMinutes:Q', title='Varighed (minutter)'),
            color=alt.Color('AgentDisplayName:N', title='Medarbejder'),
            tooltip=[
                alt.Tooltip('TimeInterval:T', title='Tidspunkt', format='%H:%M'),
                alt.Tooltip('DurationMinutes:Q', title='Varighed (minutter)'),
                alt.Tooltip('AgentDisplayName:N', title='Medarbejder')
            ]
        ).properties(
            height=700,
            width=900
        )
        st.altair_chart(chart, use_container_width=True)

    if content_tabs == 'Uge':
        unique_years = historical_data['StartTimeDenmark'].dt.year.unique()
        selected_year_week = st.selectbox(
            "Vælg et år",
            unique_years,
            format_func=lambda x: f'{x}',
            index=unique_years.tolist().index(st.session_state['selected_year_week']) if 'selected_year_week' in st.session_state and st.session_state['selected_year_week'] is not None else 0,
            key='year_select_week'
        )

        unique_weeks = historical_data[historical_data['StartTimeDenmark'].dt.year == selected_year_week]['StartTimeDenmark'].dt.isocalendar().week.unique()

        if 'selected_week' not in st.session_state or st.session_state['selected_week'] not in unique_weeks:
            st.session_state['selected_week'] = unique_weeks[0] if unique_weeks else None

        selected_week = st.selectbox(
            "Vælg en uge",
            unique_weeks,
            format_func=lambda x: f'Uge {x}',
            index=unique_weeks.tolist().index(st.session_state['selected_week']) if 'selected_week' in st.session_state and st.session_state['selected_week'] is not None else 0,
            key='week_select'
        )

        st.session_state['selected_year_week'] = selected_year_week
        st.session_state['selected_week'] = selected_week

        start_of_week = pd.to_datetime(f'{selected_year_week}-W{int(selected_week)}-1', format='%Y-W%W-%w')
        end_of_week = start_of_week + pd.Timedelta(days=6)

        historical_data_week = historical_data[
            (historical_data['StartTimeDenmark'] >= start_of_week) &
            (historical_data['StartTimeDenmark'] <= end_of_week) &
            (historical_data['StartTimeDenmark'].dt.time.between(
                datetime.strptime('05:00', '%H:%M').time(),
                datetime.strptime('16:00', '%H:%M').time()
            ))
        ]

        avg_duration_week = historical_data_week[historical_data_week['Result'] == 'Answered']['DurationMinutes'].mean()

        st.metric(label="Gennemsnitlig varighed af besvarede opkald(Uge)", value=convert_minutes_to_hms(avg_duration_week))

        chart_data = historical_data_week[['StartTimeDenmark', 'DurationMinutes', 'AgentDisplayName']]

        chart_data = chart_data.dropna(subset=['DurationMinutes', 'AgentDisplayName'])

        day_name_map = {
            'Monday': 'Mandag',
            'Tuesday': 'Tirsdag',
            'Wednesday': 'Onsdag',
            'Thursday': 'Torsdag',
            'Friday': 'Fredag',
            'Saturday': 'Lørdag',
            'Sunday': 'Søndag'
        }

        chart_data['DayOfWeek'] = chart_data['StartTimeDenmark'].dt.day_name()
        chart_data['DayOfWeek'] = chart_data['DayOfWeek'].map(day_name_map)

        all_weekdays = ['Mandag', 'Tirsdag', 'Onsdag', 'Torsdag', 'Fredag']
        chart_data['DayOfWeek'] = pd.Categorical(
            chart_data['DayOfWeek'],
            categories=all_weekdays,
            ordered=True
        )

        chart_data = chart_data.groupby(['DayOfWeek', 'AgentDisplayName']).agg({'DurationMinutes': 'sum'}).reset_index()

        st.write(f"## Varighed af samtale (Uge) - {selected_year_week}, Uge {selected_week}")
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('DayOfWeek:O', title='Ugedag', sort=all_weekdays),
            y=alt.Y('DurationMinutes:Q', title='Varighed (minutter)'),
            color=alt.Color('AgentDisplayName:N', title='Medarbejder'),
            tooltip=[alt.Tooltip('DayOfWeek:O', title='Ugedag'), alt.Tooltip('DurationMinutes:Q', title='Varighed (minutter)'), alt.Tooltip('AgentDisplayName:N', title='Medarbejder')]
        ).properties(
            height=700,
            width=900
        )

        st.altair_chart(chart, use_container_width=True)

    if content_tabs == 'Kvartal':
        unique_years = historical_data['StartTimeDenmark'].dt.year.unique()
        selected_year = st.selectbox("Vælg et år", unique_years, format_func=lambda x: f'År {x}', key='year_select')

        unique_quarters = historical_data[historical_data['StartTimeDenmark'].dt.year == selected_year]['StartTimeDenmark'].dt.to_period('Q').unique()
        quarter_names = {1: 'Q1', 2: 'Q2', 3: 'Q3', 4: 'Q4'}
        quarter_options = [(quarter.quarter, quarter_names[quarter.quarter]) for quarter in unique_quarters]
        selected_quarter = st.selectbox("Vælg et kvartal", quarter_options, format_func=lambda x: x[1], key='quarter_select')

        selected_quarter_number = selected_quarter[0]

        historical_data_quarter = historical_data[historical_data['StartTimeDenmark'].dt.to_period('Q') == pd.Period(year=selected_year, quarter=selected_quarter_number, freq='Q')]

        avg_duration_quarter = historical_data_quarter[historical_data_quarter['Result'] == 'Answered']['DurationMinutes'].mean()

        st.metric(label="Gennemsnitlig varighed af besvarede opkald(Kvartal)", value=convert_minutes_to_hms(avg_duration_quarter))

        chart_data = historical_data_quarter[['StartTimeDenmark', 'DurationMinutes', 'AgentDisplayName']]

        st.write(f"## Varighed af samtale(Kvartal) - {quarter_names[selected_quarter_number]} {selected_year}")
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('StartTimeDenmark:T', title='Tidspunkt', axis=alt.Axis(format='%Y-%m-%d %H:%M')),
            y=alt.Y('DurationMinutes:Q', title='Varighed (minutter)'),
            color=alt.Color('AgentDisplayName:N', title='Medarbejder'),
            tooltip=[alt.Tooltip('StartTimeDenmark:T', title='Tidspunkt', format='%Y-%m-%d %H:%M'), alt.Tooltip('DurationMinutes:Q', title='Varighed (minutter)'), alt.Tooltip('AgentDisplayName:N', title='Medarbejder')]
        ).properties(
            height=500
        ).facet(
            facet=alt.Facet('AgentDisplayName:N', title='Medarbejder'),
            columns=1
        )
        st.altair_chart(chart, use_container_width=True)
