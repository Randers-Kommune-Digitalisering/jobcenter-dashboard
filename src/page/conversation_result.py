import streamlit as st
import streamlit_antd_components as sac
import altair as alt
from datetime import datetime
import pandas as pd
from utils.zylinc_data import load_and_process_data_from_zylinc_db, get_all_queues_with_tables
import streamlit_shadcn_ui as ui


def show_conversation_result():
    queue_table_mapping = get_all_queues_with_tables()
    all_queues = list(queue_table_mapping.keys())

    selected_queue = st.selectbox("Vælg en kø", all_queues, key='queue_select')

    selected_table = queue_table_mapping[selected_queue]

    historical_data = load_and_process_data_from_zylinc_db(table_name=selected_table, queue_name=selected_queue)
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
        selected_date = st.date_input("Vælg en dato", min_value=min(unique_dates), max_value=max(unique_dates), key='date_input')

        historical_data_today = historical_data[
            (historical_data['StartTimeDenmark'].dt.date == selected_date) &
            (historical_data['StartTimeDenmark'].dt.time.between(
                datetime.strptime('06:00', '%H:%M').time(),
                datetime.strptime('16:00', '%H:%M').time()
            ))
        ]

        answered_calls_today = historical_data_today[historical_data_today['Result'] == 'Answered'].shape[0]
        missed_calls_today = historical_data_today[historical_data_today['Result'] == 'Missed'].shape[0]
        received_calls_today = answered_calls_today + missed_calls_today

        st.metric(label="Antal modtagne opkald", value=received_calls_today)
        st.metric(label="Antal besvarede opkald", value=answered_calls_today)
        st.metric(label="Antal mistede opkald", value=missed_calls_today)

        historical_data_today['TimeInterval'] = historical_data_today['StartTimeDenmark'].dt.floor('30T')
        interval_data = historical_data_today.groupby(['TimeInterval', 'Result']).size().reset_index(name='Antal opkald')

        interval_data['TimeInterval_Result'] = interval_data['TimeInterval'].astype(str) + '_' + interval_data['Result']

        st.write(f"## Resultat af opkald (Dag) - {selected_date}")

        chart = alt.Chart(interval_data).mark_bar().encode(
            x=alt.X('TimeInterval_Result:N', title='Tidspunkt', axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('Antal opkald:Q', title='Antal opkald'),
            color='Result:N',
            tooltip=[alt.Tooltip('TimeInterval:T', title='Tidspunkt', format='%H:%M'), alt.Tooltip('Antal opkald:Q', title='Antal opkald'), alt.Tooltip('Result:N', title='Resultat')]
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

        historical_data_week = historical_data[(historical_data['StartTimeDenmark'] >= start_of_week) & (historical_data['StartTimeDenmark'] <= end_of_week)]

        answered_calls_week = historical_data_week[historical_data_week['Result'] == 'Answered'].shape[0]
        missed_calls_week = historical_data_week[historical_data_week['Result'] == 'Missed'].shape[0]
        received_calls_week = answered_calls_week + missed_calls_week

        st.metric(label="Antal modtagne opkald", value=received_calls_week)
        st.metric(label="Antal besvarede opkald", value=answered_calls_week)
        st.metric(label="Antal mistede opkald", value=missed_calls_week)

        historical_data_week['Day'] = historical_data_week['StartTimeDenmark'].dt.floor('D')
        daily_data = historical_data_week.groupby(['Day', 'Result']).size().reset_index(name='Antal opkald')

        daily_data['DayOfWeek'] = daily_data['Day'].dt.day_name()

        day_name_map = {
            'Monday': 'Mandag',
            'Tuesday': 'Tirsdag',
            'Wednesday': 'Onsdag',
            'Thursday': 'Torsdag',
            'Friday': 'Fredag',
            'Saturday': 'Lørdag',
            'Sunday': 'Søndag'
        }
        daily_data['DayOfWeek'] = daily_data['DayOfWeek'].map(day_name_map)

        all_weekdays = ['Mandag', 'Tirsdag', 'Onsdag', 'Torsdag', 'Fredag']
        daily_data['DayOfWeek'] = pd.Categorical(
            daily_data['DayOfWeek'],
            categories=all_weekdays,
            ordered=True
        )

        st.write(f"## Resultat af opkald (Uge) - {selected_year_week}, Uge {selected_week}")

        chart = alt.Chart(daily_data).mark_bar().encode(
            x=alt.X('DayOfWeek:O', title='Ugedag', sort=all_weekdays),
            y='Antal opkald:Q',
            color='Result:N',
        )

        st.altair_chart(chart, use_container_width=True)

    if content_tabs == 'Måned':
        unique_years = historical_data['StartTimeDenmark'].dt.year.unique()
        selected_year_month = st.selectbox(
            "Vælg et år",
            unique_years,
            format_func=lambda x: f'{x}',
            index=unique_years.tolist().index(st.session_state['selected_year_month']) if 'selected_year_month' in st.session_state and st.session_state['selected_year_month'] is not None else 0,
            key='year_select_month'
        )

        unique_months = historical_data[historical_data['StartTimeDenmark'].dt.year == selected_year_month]['StartTimeDenmark'].dt.to_period('M').unique()
        month_names = {1: 'Januar', 2: 'Februar', 3: 'Marts', 4: 'April', 5: 'Maj', 6: 'Juni', 7: 'Juli', 8: 'August', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'December'}
        month_options = [(month.month, month_names[month.month]) for month in unique_months]

        if 'selected_month' not in st.session_state or st.session_state['selected_month'] is None:
            st.session_state['selected_month'] = month_options[0][0] if month_options else None

        selected_month = st.selectbox(
            "Vælg en måned",
            month_options,
            format_func=lambda x: x[1],
            index=[month[0] for month in month_options].index(st.session_state['selected_month']) if 'selected_month' in st.session_state and st.session_state['selected_month'] is not None else 0,
            key='month_select'
        )

        st.session_state['selected_year_month'] = selected_year_month
        st.session_state['selected_month'] = selected_month[0]

        selected_month_number = selected_month[0]

        historical_data_month = historical_data[historical_data['StartTimeDenmark'].dt.to_period('M') == pd.Period(year=selected_year_month, month=selected_month_number, freq='M')]

        answered_calls_month = historical_data_month[historical_data_month['Result'] == 'Answered'].shape[0]
        missed_calls_month = historical_data_month[historical_data_month['Result'] == 'Missed'].shape[0]
        received_calls_month = answered_calls_month + missed_calls_month

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            ui.metric_card(
                title="Antal modtagne opkald",
                content=int(received_calls_month),
                description=f"Samlet antal opkald modtaget i {month_names[selected_month_number]} {selected_year_month}."
            )

        with col2:
            ui.metric_card(
                title="Antal besvarede opkald",
                content=int(answered_calls_month),
                description=f"Samlet antal opkald besvaret i {month_names[selected_month_number]} {selected_year_month}."
            )

        with col3:
            ui.metric_card(
                title="Antal mistede opkald",
                content=int(missed_calls_month),
                description=f"Samlet antal opkald mistet i {month_names[selected_month_number]} {selected_year_month}."
            )

        historical_data_month['Day'] = historical_data_month['StartTimeDenmark'].dt.floor('D')
        daily_data = historical_data_month.groupby(['Day', 'Result']).size().reset_index(name='Antal opkald')
        daily_data['Day'] = daily_data['Day'].dt.day

        st.write(f"## Resultat af opkald (Måned) - {selected_year_month}, Måned {month_names[selected_month_number]}")

        chart = alt.Chart(daily_data).mark_bar().encode(
            x=alt.X('Day:O', title='Månedsdag'),
            y='Antal opkald:Q',
            color='Result:N'
        )

        st.altair_chart(chart, use_container_width=True)
