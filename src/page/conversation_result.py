import streamlit as st
import streamlit_antd_components as sac
import altair as alt
from datetime import datetime
import pandas as pd
from utils.zylinc_data import load_and_process_data_from_zylinc_db, get_all_queues_with_tables


def show_conversation_result():
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
            sac.TabsItem('Dag', tag='Dag', icon='calendar-day'),
            sac.TabsItem('Uge', tag='Uge', icon='calendar-week'),
            sac.TabsItem('Måned', tag='Måned', icon='calendar-month'),
            sac.TabsItem('Kvartal', tag='Kvartal', icon='bi bi-calendar-minus'),
            sac.TabsItem('Halvår', tag='Halvår', icon='calendar'),
        ], color='dark', size='md', position='top', align='start', use_container_width=True)

    if content_tabs == 'Dag':
        unique_dates = sorted(historical_data['StartTimeDenmark'].dt.date.unique())

        if len(unique_dates) == 0:
            st.error("Ingen data tilgængelig for den valgte kø.")
            st.stop()

        default_end = max(unique_dates)
        if len(unique_dates) > 6:
            default_start = unique_dates[-7]
        else:
            default_start = min(unique_dates)

        periode_mode = st.toggle("Brugerdefineret periode", value=False)

        if periode_mode:
            st.subheader("Vælg periode")
            col1, col2 = st.columns(2)

            session_start = st.session_state.get('start_date', default_start)
            if session_start < min(unique_dates) or session_start > max(unique_dates):
                session_start = default_start
            session_end = st.session_state.get('end_date', default_end)
            if session_end < min(unique_dates) or session_end > max(unique_dates):
                session_end = default_end

            with col1:
                start_date = st.date_input(
                    "Startdato",
                    value=session_start,
                    min_value=min(unique_dates),
                    max_value=max(unique_dates),
                    key='start_date'
                )
            with col2:
                end_date = st.date_input(
                    "Slutdato",
                    value=session_end,
                    min_value=min(unique_dates),
                    max_value=max(unique_dates),
                    key='end_date'
                )

            if start_date > end_date:
                st.warning("Startdato må ikke være efter slutdato.")
            else:
                mask = (
                    (historical_data['StartTimeDenmark'].dt.date >= start_date) &
                    (historical_data['StartTimeDenmark'].dt.date <= end_date) &
                    (historical_data['StartTimeDenmark'].dt.time.between(
                        datetime.strptime('05:00', '%H:%M').time(),
                        datetime.strptime('18:00', '%H:%M').time()
                    ))
                )
                period_data = historical_data[mask]
                answered_calls_period = period_data[period_data['Result'] == 'Answered'].shape[0]
                missed_calls_period = period_data[period_data['Result'] == 'Missed'].shape[0]
                received_calls_period = answered_calls_period + missed_calls_period

                col1, col2, col3 = st.columns([1, 1, 1])

                with col1:
                    st.metric(
                        label="Antal modtagne opkald (Periode)",
                        value=int(received_calls_period),
                        help=f"Samlet antal opkald modtaget fra {start_date.strftime('%d-%m-%Y')} til {end_date.strftime('%d-%m-%Y')}.",
                        border=True
                    )

                with col2:
                    st.metric_card(
                        label="Antal besvarede opkald (Periode)",
                        value=int(answered_calls_period),
                        help=f"Samlet antal opkald besvaret fra {start_date.strftime('%d-%m-%Y')} til {end_date.strftime('%d-%m-%Y')}.",
                        border=True
                    )

                with col3:
                    st.metric(
                        label="Antal mistede opkald (Periode)",
                        value=int(missed_calls_period),
                        help=f"Samlet antal opkald mistet fra {start_date.strftime('%d-%m-%Y')} til {end_date.strftime('%d-%m-%Y')}.",
                        border=True
                    )

                if not period_data.empty:
                    if start_date == end_date:
                        period_data['TimeInterval'] = period_data['StartTimeDenmark'].dt.floor('30T')
                        interval_data = period_data.groupby(['TimeInterval', 'Result']).size().reset_index(name='Antal opkald')
                        st.write(f"## Resultat af opkald pr. tid ({start_date.strftime('%d-%m-%Y')})")
                        chart = alt.Chart(interval_data).mark_bar().encode(
                            x=alt.X('TimeInterval:T', title='Tidspunkt', axis=alt.Axis(format='%H:%M')),
                            y=alt.Y('Antal opkald:Q', title='Antal opkald'),
                            color='Result:N',
                            tooltip=[
                                alt.Tooltip('TimeInterval:T', title='Tidspunkt', format='%H:%M'),
                                alt.Tooltip('Antal opkald:Q', title='Antal opkald'),
                                alt.Tooltip('Result:N', title='Resultat')
                            ]
                        ).properties(height=400, width=800)
                    else:
                        period_data['Date'] = period_data['StartTimeDenmark'].dt.date
                        daily_data = period_data.groupby(['Date', 'Result']).size().reset_index(name='Antal opkald')
                        st.write(f"## Resultat af opkald pr. dag ({start_date.strftime('%d-%m-%Y')} – {end_date.strftime('%d-%m-%Y')})")
                        chart = alt.Chart(daily_data).mark_bar().encode(
                            x=alt.X('Date:T', title='Dato'),
                            y=alt.Y('Antal opkald:Q', title='Antal opkald'),
                            color='Result:N',
                            tooltip=[
                                alt.Tooltip('Date:T', title='Dato', format='%d-%m-%Y'),
                                alt.Tooltip('Antal opkald:Q', title='Antal opkald'),
                                alt.Tooltip('Result:N', title='Resultat')
                            ]
                        ).properties(height=400, width=800)
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("Ingen opkald i den valgte periode.")
        else:
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

            answered_calls_today = historical_data_today[historical_data_today['Result'] == 'Answered'].shape[0]
            missed_calls_today = historical_data_today[historical_data_today['Result'] == 'Missed'].shape[0]
            received_calls_today = answered_calls_today + missed_calls_today

            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                st.metric(
                    label="Antal modtagne opkald",
                    value=int(received_calls_today),
                    help=f"Samlet antal opkald modtaget den {selected_date}.",
                    border=True
                )

            with col2:
                st.metric(
                    label="Antal besvarede opkald",
                    value=int(answered_calls_today),
                    help=f"Samlet antal opkald besvaret den {selected_date}.",
                    border=True
                )

            with col3:
                st.metric(
                    label="Antal mistede opkald",
                    value=int(missed_calls_today),
                    help=f"Samlet antal opkald mistet den {selected_date}.",
                    border=True
                )

            historical_data_today["Result"] = historical_data_today["Result"].replace({
                "Answered": "Besvaret",
                "Missed": "Ikke besvaret"
            })

            historical_data_today['TimeInterval'] = historical_data_today['StartTimeDenmark'].dt.floor('30T')
            interval_data = historical_data_today.groupby(['TimeInterval', 'Result']).size().reset_index(name='Antal opkald')

            st.header(f"Resultat af opkald (Dag) - {selected_date}", divider="gray")
            chart = alt.Chart(interval_data).mark_bar().encode(
                x=alt.X('TimeInterval:T', title='Tidspunkt', axis=alt.Axis(format='%H:%M')),
                y=alt.Y('Antal opkald:Q', title='Antal opkald'),
                color=alt.Color('Result:N', title='Resultat'),
                tooltip=[
                    alt.Tooltip('TimeInterval:T', title='Tidspunkt', format='%H:%M'),
                    alt.Tooltip('Antal opkald:Q', title='Antal opkald'),
                    alt.Tooltip('Result:N', title='Resultat')
                ]
            ).properties(
                height=700,
                width=900
            )

            st.altair_chart(chart, use_container_width=True)

    if content_tabs == 'Uge':
        unique_years = sorted(historical_data['StartTimeDenmark'].dt.year.unique())

        if len(unique_years) == 0:
            st.error("Ingen data tilgængelig for den valgte kø.")
            st.stop()

        default_year = max(unique_years)
        session_year = st.session_state.get('selected_year_weeks', default_year)

        if session_year not in unique_years:
            session_year = default_year

        selected_year_week = st.selectbox("Vælg år", unique_years, key='selected_year_week', index=unique_years.index(session_year))
        unique_weeks = sorted(historical_data[historical_data['StartTimeDenmark'].dt.year == selected_year_week]['StartTimeDenmark'].dt.isocalendar().week.unique())

        if len(unique_weeks) == 0:
            st.error("Ingen uger med data for valgt år.")
            st.stop()

        default_week = max(unique_weeks)
        session_week = st.session_state.get('selected_week', default_week)

        if session_week not in unique_weeks:
            session_week = default_week

        selected_week = st.selectbox("Vælg uge", unique_weeks, key='selected_week', index=unique_weeks.index(session_week))
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

        answered_calls_week = historical_data_week[historical_data_week['Result'] == 'Answered'].shape[0]
        missed_calls_week = historical_data_week[historical_data_week['Result'] == 'Missed'].shape[0]
        received_calls_week = answered_calls_week + missed_calls_week

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.metric(
                label="Antal modtagne opkald",
                value=int(received_calls_week),
                help=f"Samlet antal opkald modtaget i Uge {selected_week}.",
                border=True
            )

        with col2:
            st.metric(
                label="Antal besvarede opkald",
                value=int(answered_calls_week),
                help=f"Samlet antal opkald besvaret i Uge {selected_week}.",
                border=True
            )

        with col3:
            st.metric(
                label="Antal mistede opkald",
                value=int(missed_calls_week),
                help=f"Samlet antal opkald mistet i Uge {selected_week}.",
                border=True
            )

        historical_data_week["Result"] = historical_data_week["Result"].replace({
            "Answered": "Besvaret",
            "Missed": "Ikke besvaret"
        })

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

        st.header(f"Resultat af opkald (Uge) - {selected_year_week}, Uge {selected_week}", divider="gray")
        chart = alt.Chart(daily_data).mark_bar().encode(
            x=alt.X('DayOfWeek:O', title='Ugedag', sort=all_weekdays),
            y='Antal opkald:Q',
            color=alt.Color('Result:N', title='Resultat'),
        )

        st.altair_chart(chart, use_container_width=True)

    if content_tabs == 'Måned':
        unique_years = sorted(historical_data['StartTimeDenmark'].dt.year.unique())

        if len(unique_years) == 0:
            st.error("Ingen data tilgængelig for den valgte kø.")
            st.stop()

        default_year = max(unique_years)
        session_year = st.session_state.get('year_select_activity_month', default_year)

        if session_year not in unique_years:
            session_year = default_year

        selected_year_month = st.selectbox("Vælg år", unique_years, key='year_select_activity_month', index=unique_years.index(session_year))
        unique_months = sorted(historical_data[historical_data['StartTimeDenmark'].dt.year == selected_year_month]['StartTimeDenmark'].dt.month.unique())
        month_names = {1: 'Januar', 2: 'Februar', 3: 'Marts', 4: 'April', 5: 'Maj', 6: 'Juni', 7: 'Juli', 8: 'August', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'December'}

        if len(unique_months) == 0:
            st.error("Ingen måneder med data for valgt år.")
            st.stop()

        default_month = max(unique_months)
        session_month = st.session_state.get('month_select_activity', default_month)

        if session_month not in unique_months:
            session_month = default_month

        selected_month = st.selectbox("Vælg måned", unique_months, format_func=lambda x: month_names[x], key='month_select_activity', index=unique_months.index(session_month))
        historical_data_month = historical_data[
            (historical_data['StartTimeDenmark'].dt.year == selected_year_month) &
            (historical_data['StartTimeDenmark'].dt.month == selected_month) &
            (historical_data['StartTimeDenmark'].dt.time.between(
                datetime.strptime('05:00', '%H:%M').time(),
                datetime.strptime('18:00', '%H:%M').time()
            ))
        ]

        answered_calls_month = historical_data_month[historical_data_month['Result'] == 'Answered'].shape[0]
        missed_calls_month = historical_data_month[historical_data_month['Result'] == 'Missed'].shape[0]
        received_calls_month = answered_calls_month + missed_calls_month

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.metric(
                label="Antal modtagne opkald",
                value=int(received_calls_month),
                help=f"Samlet antal opkald modtaget i {month_names[selected_month]} {selected_year_month}.",
                border=True
            )

        with col2:
            st.metric(
                label="Antal besvarede opkald",
                value=int(answered_calls_month),
                help=f"Samlet antal opkald besvaret i {month_names[selected_month]} {selected_year_month}.",
                border=True
            )

        with col3:
            st.metric(
                label="Antal mistede opkald",
                value=int(missed_calls_month),
                help=f"Samlet antal opkald mistet i {month_names[selected_month]} {selected_year_month}.",
                border=True
            )

        historical_data_month["Result"] = historical_data_month["Result"].replace({
            "Answered": "Besvaret",
            "Missed": "Ikke besvaret"
        })

        historical_data_month['Day'] = historical_data_month['StartTimeDenmark'].dt.floor('D')
        daily_data = historical_data_month.groupby(['Day', 'Result']).size().reset_index(name='Antal opkald')
        daily_data['Day'] = daily_data['Day'].dt.day

        st.header(f"Resultat af opkald (Måned) - {selected_year_month}, Måned {month_names[selected_month]}", divider="gray")
        chart = alt.Chart(daily_data).mark_bar().encode(
            x=alt.X('Day:O', title='Månedsdag'),
            y='Antal opkald:Q',
            color=alt.Color('Result:N', title='Resultat'),
        )

        st.altair_chart(chart, use_container_width=True)

    if content_tabs == 'Kvartal':
        unique_years = historical_data['StartTimeDenmark'].dt.year.unique()

        if 'selected_year_quarter' in st.session_state:
            if st.session_state['selected_year_quarter'] not in unique_years:
                st.session_state['selected_year_quarter'] = max(unique_years)

        selected_year_quarter = st.selectbox(
            "Vælg et år",
            unique_years,
            format_func=lambda x: f'{x}',
            index=unique_years.tolist().index(st.session_state.get('selected_year_quarter', max(unique_years))),
            key='year_select_quarter'
        )

        historical_data['Quarter'] = historical_data['StartTimeDenmark'].dt.quarter
        unique_quarters = sorted(historical_data[historical_data['StartTimeDenmark'].dt.year == selected_year_quarter]['Quarter'].unique())
        quarter_names = {1: '1. kvartal', 2: '2. kvartal', 3: '3. kvartal', 4: '4. kvartal'}
        quarter_options = [(q, quarter_names[q]) for q in unique_quarters]

        if 'selected_quarter' not in st.session_state or st.session_state['selected_quarter'] not in [q[0] for q in quarter_options]:
            st.session_state['selected_quarter'] = max([q[0] for q in quarter_options]) if quarter_options else None

        selected_quarter = st.selectbox(
            "Vælg et kvartal",
            quarter_options,
            format_func=lambda x: x[1],
            index=[q[0] for q in quarter_options].index(st.session_state['selected_quarter']) if st.session_state['selected_quarter'] in [q[0] for q in quarter_options] else 0,
            key='quarter_select'
        )

        st.session_state['selected_year_quarter'] = selected_year_quarter
        st.session_state['selected_quarter'] = selected_quarter[0]

        selected_quarter_number = selected_quarter[0]

        historical_data_quarter = historical_data[
            (historical_data['StartTimeDenmark'].dt.year == selected_year_quarter) &
            (historical_data['Quarter'] == selected_quarter_number)
        ]

        answered_calls_quarter = historical_data_quarter[historical_data_quarter['Result'] == 'Answered'].shape[0]
        missed_calls_quarter = historical_data_quarter[historical_data_quarter['Result'] == 'Missed'].shape[0]
        received_calls_quarter = answered_calls_quarter + missed_calls_quarter

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.metric(
                label="Antal modtagne opkald",
                value=int(received_calls_quarter),
                help=f"Samlet antal opkald modtaget i {quarter_names[selected_quarter_number]} {selected_year_quarter}.",
                border=True
            )

        with col2:
            st.metric(
                label="Antal besvarede opkald",
                value=int(answered_calls_quarter),
                help=f"Samlet antal opkald besvaret i {quarter_names[selected_quarter_number]} {selected_year_quarter}.",
                border=True
            )

        with col3:
            st.metric(
                label="Antal mistede opkald",
                value=int(missed_calls_quarter),
                help=f"Samlet antal opkald mistet i {quarter_names[selected_quarter_number]} {selected_year_quarter}.",
                border=True
            )

        historical_data_quarter["Result"] = historical_data_quarter["Result"].replace({
            "Answered": "Besvaret",
            "Missed": "Ikke besvaret"
        })

        historical_data_quarter['Month'] = historical_data_quarter['StartTimeDenmark'].dt.month
        month_names = {1: 'Januar', 2: 'Februar', 3: 'Marts', 4: 'April', 5: 'Maj', 6: 'Juni', 7: 'Juli', 8: 'August', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'December'}
        monthly_data = historical_data_quarter.groupby(['Month', 'Result']).size().reset_index(name='Antal opkald')
        monthly_data['MonthName'] = monthly_data['Month'].map(month_names)

        kvartal_måneder = {
            1: ['Januar', 'Februar', 'Marts'],
            2: ['April', 'Maj', 'Juni'],
            3: ['Juli', 'August', 'September'],
            4: ['Oktober', 'November', 'December']
        }
        current_quarter_months = kvartal_måneder[selected_quarter_number]

        st.header(f"Resultat af opkald (Kvartal) - {selected_year_quarter}, {quarter_names[selected_quarter_number]}", divider="gray")
        chart = alt.Chart(monthly_data).mark_bar().encode(
            x=alt.X('MonthName:O', title='Måned', sort=current_quarter_months),
            y='Antal opkald:Q',
            color=alt.Color('Result:N', title='Resultat'),
        )

        st.altair_chart(chart, use_container_width=True)

    if content_tabs == 'Halvår':
        unique_years = historical_data['StartTimeDenmark'].dt.year.unique()

        if 'selected_year_half' in st.session_state:
            if st.session_state['selected_year_half'] not in unique_years:
                st.session_state['selected_year_half'] = max(unique_years)

        selected_year_half = st.selectbox(
            "Vælg et år",
            unique_years,
            format_func=lambda x: f'{x}',
            index=unique_years.tolist().index(st.session_state.get('selected_year_half', max(unique_years))),
            key='year_select_half'
        )

        historical_data['Half'] = historical_data['StartTimeDenmark'].dt.month.apply(lambda m: 1 if m <= 6 else 2)
        half_names = {1: '1. halvår', 2: '2. halvår'}
        unique_halves = sorted(historical_data[historical_data['StartTimeDenmark'].dt.year == selected_year_half]['Half'].unique())
        half_options = [(h, half_names[h]) for h in unique_halves]

        if 'selected_half' not in st.session_state or st.session_state['selected_half'] not in [h[0] for h in half_options]:
            st.session_state['selected_half'] = min([h[0] for h in half_options]) if half_options else None

        selected_half = st.selectbox(
            "Vælg et halvår",
            half_options,
            format_func=lambda x: x[1],
            index=[h[0] for h in half_options].index(st.session_state['selected_half']) if st.session_state['selected_half'] in [h[0] for h in half_options] else 0,
            key='half_select'
        )

        st.session_state['selected_year_half'] = selected_year_half
        st.session_state['selected_half'] = selected_half[0]

        selected_half_number = selected_half[0]

        historical_data_half = historical_data[
            (historical_data['StartTimeDenmark'].dt.year == selected_year_half) &
            (historical_data['Half'] == selected_half_number)
        ]

        answered_calls_half = historical_data_half[historical_data_half['Result'] == 'Answered'].shape[0]
        missed_calls_half = historical_data_half[historical_data_half['Result'] == 'Missed'].shape[0]
        received_calls_half = answered_calls_half + missed_calls_half

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.metric(
                label="Antal modtagne opkald",
                value=int(received_calls_half),
                help=f"Samlet antal opkald modtaget i {half_names[selected_half_number]} {selected_year_half}.",
                border=True
            )

        with col2:
            st.metric(
                label="Antal besvarede opkald",
                value=int(answered_calls_half),
                help=f"Samlet antal opkald besvaret i {half_names[selected_half_number]} {selected_year_half}.",
                border=True
            )

        with col3:
            st.metric(
                label="Antal mistede opkald",
                value=int(missed_calls_half),
                help=f"Samlet antal opkald mistet i {half_names[selected_half_number]} {selected_year_half}.",
                border=True
            )

        historical_data_half["Result"] = historical_data_half["Result"].replace({
            "Answered": "Besvaret",
            "Missed": "Ikke besvaret"
        })

        historical_data_half['Month'] = historical_data_half['StartTimeDenmark'].dt.month
        month_names = {1: 'Januar', 2: 'Februar', 3: 'Marts', 4: 'April', 5: 'Maj', 6: 'Juni', 7: 'Juli', 8: 'August', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'December'}
        monthly_data = historical_data_half.groupby(['Month', 'Result']).size().reset_index(name='Antal opkald')
        monthly_data['MonthName'] = monthly_data['Month'].map(month_names)

        halv_måneder = {
            1: ['Januar', 'Februar', 'Marts', 'April', 'Maj', 'Juni'],
            2: ['Juli', 'August', 'September', 'Oktober', 'November', 'December']
        }
        current_half_months = halv_måneder[selected_half_number]

        st.header(f"Resultat af opkald (Halvår) - {selected_year_half}, {half_names[selected_half_number]}", divider="gray")
        chart = alt.Chart(monthly_data).mark_bar().encode(
            x=alt.X('MonthName:O', title='Måned', sort=current_half_months),
            y='Antal opkald:Q',
            color=alt.Color('Result:N', title='Resultat'),
        )

        st.altair_chart(chart, use_container_width=True)
