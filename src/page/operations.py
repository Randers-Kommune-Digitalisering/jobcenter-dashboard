import streamlit as st
import altair as alt
import pandas as pd
import numpy as np

import datetime as dt
from sqlalchemy import create_engine
from utils.utility_functions import format_timedelta_in_danish, decimalMinutesToStr, timedelta_to_minutes

# # Uncomment when using database
from utils.config import POSTGRES_DB_USER, POSTGRES_DB_PASS, POSTGRES_DB_HOST, POSTGRES_DB_DATABASE
db_client = create_engine(f'postgresql+psycopg2://{POSTGRES_DB_USER}:{POSTGRES_DB_PASS}@{POSTGRES_DB_HOST}/{POSTGRES_DB_DATABASE}')

operations = pd.read_sql('SELECT * FROM operationsjobcenter', db_client)

operations["CreatedAt"] = pd.to_datetime(operations["CreatedAt"])
operations["CalledAt"] = pd.to_datetime(operations["CalledAt"])
operations["EndedAt"] = pd.to_datetime(operations["EndedAt"])
operations["dato"] = pd.to_datetime(operations["CreatedAt"]).dt.date
operations["year"] = pd.to_datetime(operations["CreatedAt"]).dt.year
operations["ugenr"] = pd.to_datetime(operations["CreatedAt"]).dt.isocalendar().week
# operations["QueueName"] = operations["QueueName"].str.strip()
# operations["EmployeeName"] = operations["EmployeeName"].str.strip()
operations["Ventetid"] = (operations["CalledAt"] - operations["CreatedAt"]).apply(format_timedelta_in_danish)
operations["Betjeningstid"] = (operations["EndedAt"] - operations["CalledAt"]).apply(format_timedelta_in_danish)

currentYear = dt.datetime.now().year
lastYear = currentYear - 1
currentWeek = dt.datetime.now().isocalendar().week
latestWeekOperations = operations[(operations["år"] == currentYear)]["ugenr"].max()

latestDateOperations = operations["CreatedAt"].max()
latestDateOperations = latestDateOperations.date()

employees = operations["EmployeeName"].unique()
employees = [str(employee) for employee in employees]

colorScale = alt.Scale(
    domain=["Betjeninger sidste år", "Betjeninger i år"],
    range=["#83C9FF", "#0068C9"]
)

operations = operations[operations["State"] != "Discarded"]
operations = operations.drop(columns=["MunicipalityID", "QueueId", "State", "StateId", "CounterId", "EmployeeId", "DelayedUntil", "DelayedFrom", "IsEmployeeAnonymized", "EmployeeInitials"])


def show_operations():
    # st.write(operations)

    # Number of operations last year by week
    dfGraph = operations.groupby(["ugenr", "year"]).size().reset_index(name="antal")
    dfGraph = dfGraph[dfGraph["year"] >= lastYear]

    dfGraph["operations"] = np.where(dfGraph["year"] == lastYear, dfGraph["antal"], pd.NA)
    dfGraph["series"] = np.where(dfGraph["year"] == lastYear, "Betjeninger sidste år", pd.NA)
    dfGraph["operations"] = np.where((dfGraph["year"] == currentYear), dfGraph["antal"], dfGraph["operations"])
    dfGraph["series"] = np.where((dfGraph["year"] == currentYear), "Betjeninger i år", dfGraph["series"])

    weekly_operations_chart = alt.Chart(dfGraph).mark_line().encode(
        x=alt.X('ugenr', title='Uge', scale=alt.Scale(domain=[1, dfGraph["ugenr"].max()]), axis=alt.Axis(values=[1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, dfGraph["ugenr"].max()])),
        y=alt.Y('operations', title='Betjeninger'),
        color=alt.Color('series', scale=colorScale, legend=alt.Legend(orient='bottom', title=None, labelFontSize=12, titleFontSize=14)),
        strokeDash=alt.condition(
            alt.datum.series == 'Forecast i år',
            alt.value([5, 5]),  # Dashed line for forecast
            alt.value([0])  # Solid line for others
        ),
        strokeWidth=alt.condition(
            alt.datum.series == 'Forecast i år',
            alt.value(1),  # Thicker line for forecast
            alt.value(1)  # Thinner line for others
        ),
        tooltip=['ugenr', 'operations']
    )

    sumOperationsLastYear = dfGraph.loc[(dfGraph["series"] == "Betjeninger sidste år"), "antal"].sum()
    sumOperationsCurrentYear = dfGraph.loc[(dfGraph["series"] == "Betjeninger i år"), "antal"].sum()

    # Display in Streamlit
    st.markdown("### Samlet antal betjeninger")
    st.write(f"Samlet antal betjeninger sidste år: __{sumOperationsLastYear:,.0f}__. Antal betjeninger i år: __{sumOperationsCurrentYear:,.0f}__.".replace(",", "."))
    st.altair_chart(weekly_operations_chart, use_container_width=True)

    # Betjeningingstid
    st.markdown("### Betjeningingstid indeværende år")

    # Filter data for the latest year (current year)
    operationsCurrentYear = operations[operations["year"] == currentYear]

    # Convert "Betjeningstid" to numeric values
    operationsCurrentYear["Betjeningstid_minutes"] = operationsCurrentYear["Betjeningstid"].apply(timedelta_to_minutes)

    betjeningstidGennemsnit = operationsCurrentYear["Betjeningstid_minutes"].mean()

    # Create a histogram using Altair
    betjeningstid_histogram = alt.Chart(operationsCurrentYear).mark_bar().encode(
        x=alt.X('Betjeningstid_minutes:Q', bin=alt.Bin(maxbins=30), title='Betjeningstid (minutter)'),
        y=alt.Y('count()', title='Betjeninger'),
        tooltip=['count()']
    )
    # Display the histogram in Streamlit
    st.write(f"Gennemsnitlig ventetid: {decimalMinutesToStr(betjeningstidGennemsnit)}.")
    st.altair_chart(betjeningstid_histogram, use_container_width=True)

    # Ventetid
    operationsCurrentYear["Ventetid_minutes"] = operationsCurrentYear["Ventetid"].apply(timedelta_to_minutes)

    ventetidGennemsnit = operationsCurrentYear["Ventetid_minutes"].mean()

    # Create a histogram using Altair
    Ventetid_histogram = alt.Chart(operationsCurrentYear).mark_bar().encode(
        x=alt.X('Ventetid_minutes:Q', bin=alt.Bin(maxbins=30), title='Ventetid (minutter)'),
        y=alt.Y('count()', title='Betjeninger'),
        tooltip=['count()']
    )
    # Display the histogram in Streamlit
    st.markdown("### Ventetid indeværende år")
    st.write(f"Gennemsnitlig ventetid: {decimalMinutesToStr(ventetidGennemsnit)}.")
    st.altair_chart(Ventetid_histogram, use_container_width=True)
