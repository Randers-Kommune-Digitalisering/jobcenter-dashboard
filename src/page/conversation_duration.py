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
            sac.TabsItem('Måned', tag='Måned'),
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

    if content_tabs == 'Måned':
        unique_years = historical_data['StartTimeDenmark'].dt.year.unique()

        if len(unique_years) == 0:
            st.error("Ingen data tilgængelig for den valgte kø.")
            st.stop()

        if 'selected_year_month' in st.session_state:
            if st.session_state['selected_year_month'] not in unique_years:
                st.session_state['selected_year_month'] = max(unique_years)

        selected_year_month = st.selectbox(
            "Vælg et år",
            unique_years,
            format_func=lambda x: f'{x}',
            index=unique_years.tolist().index(st.session_state.get('selected_year_month', max(unique_years))),
            key='year_select_month'
        )

        unique_months = historical_data[historical_data['StartTimeDenmark'].dt.year == selected_year_month]['StartTimeDenmark'].dt.to_period('M').unique()
        month_names = {1: 'Januar', 2: 'Februar', 3: 'Marts', 4: 'April', 5: 'Maj', 6: 'Juni', 7: 'Juli', 8: 'August', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'December'}
        month_options = [(month.month, month_names[month.month]) for month in unique_months]

        if 'selected_month' not in st.session_state or st.session_state['selected_month'] not in [month[0] for month in month_options]:
            st.session_state['selected_month'] = max([month[0] for month in month_options]) if month_options else None

        selected_month = st.selectbox(
            "Vælg en måned",
            month_options,
            format_func=lambda x: x[1],
            index=[month[0] for month in month_options].index(st.session_state['selected_month']) if st.session_state['selected_month'] in [month[0] for month in month_options] else 0,
            key='month_select'
        )

        st.session_state['selected_year_month'] = selected_year_month
        st.session_state['selected_month'] = selected_month[0]

        selected_month_number = selected_month[0]

        historical_data_month = historical_data[
            historical_data['StartTimeDenmark'].dt.to_period('M') == pd.Period(year=selected_year_month, month=selected_month_number, freq='M')
        ]

        if historical_data_month.empty:
            st.error("Ingen data tilgængelig for den valgte måned.")
            st.stop()

        avg_duration_month = historical_data_month[historical_data_month['Result'] == 'Answered']['DurationMinutes'].mean()
        avg_duration_month = 0 if pd.isna(avg_duration_month) else avg_duration_month

        col1 = st.columns([1])[0]

        with col1:
            st.metric(
                label="Gennemsnitlig varighed af besvarede opkald (Måned)",
                value=convert_minutes_to_hms(avg_duration_month),
                help=f"Data for {month_names[selected_month_number]} {selected_year_month}"
            )

        historical_data_month['Day'] = historical_data_month['StartTimeDenmark'].dt.day

        daily_data = historical_data_month.groupby(['Day', 'AgentDisplayName']).agg({'DurationMinutes': 'mean'}).reset_index()

        st.write(f"## Varighed af samtale (Måned) - {month_names[selected_month_number]} {selected_year_month}")
        chart = alt.Chart(daily_data).mark_bar().encode(
            x=alt.X('Day:O', title='Dag', axis=alt.Axis(format='d')),
            y=alt.Y('DurationMinutes:Q', title='Varighed (minutter)'),
            color=alt.Color('AgentDisplayName:N', title='Medarbejder'),
            tooltip=[
                alt.Tooltip('Day:O', title='Dag'),
                alt.Tooltip('DurationMinutes:Q', title='Varighed (minutter)'),
                alt.Tooltip('AgentDisplayName:N', title='Medarbejder')
            ]
        ).properties(
            height=700,
            width=900
        )
        st.altair_chart(chart, use_container_width=True)
