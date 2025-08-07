# Jobcenter Dashboard `README.md`
[**Formål**](#formål) | [**Opbygning af dashboard**](#opbygning) | [**Afhængigheder**](#afh%C3%A6ngigheder) 

## Formål

Formålet med dashboardet er at vise opkaldsstatistik med data fra Zylinc over flere Jobcenter køer. Zylinc data for de forskellige køer hentes fra en Postgres DB, samt Live data fra Zylinc API'et

## Opbygning af dashboard
Jobcenter Dashboardet består af følgende 6 sider: 

- (`Side 1: Live Data`) Siden viser igangværende Live opkald fra Jobcenter køen som kommer fra Zylinc API'et  
- (`Side 2: Varighed af samtale`) Siden visualiserer varigheden af en samtale i en graf baseret på en specifik Dag, Uge, Måned, Kvartal og Halvår. Samt en metric til at vise den Gennemsnitlig varighed af besvarede opkald
- (`Side 3: Resultat af samtale`) Siden visualiserer resultat af en samtale(Modtaget, Besvarede og mistede) i en graf baseret på en specifik Dag, Uge, Måned, Kvartal og Halvår. Samt metrics til at vise (`Antal modtagne opkald, Antal besvarede opkald, Antal mistede opkald`)
- (`Side 4: Ventetid pr opkald`) Siden visualiserer ventetiden af et opkald i en graf baseret på en specifik Dag, Uge, Måned, Kvartal og Halvår. Samt en metric til at vise den Gennemsnitlig ventetid pr kald. 
- (`Side 5: Antal af samtaler`) Siden visualiserer antal af samtaler i en graf baseret på en specifik Dag, Uge, Måned, Kvartal og Halvår. Samt en metric til at vise antal besvarede opkald
- (`Side 6: Opkaldsaktivitet`) Siden visualiserer hvornår på dagen der har været mest travlt i en graf baseret på en specifik Dag, Uge, Måned, Kvartal og Halvår. Samt en metric til at vise det tidpunktet der har været flest opkaldsaktivitet.


**Dataflow:**
- SQL kald til Postgres DB → Zylinc API → Visualiserer data

## Afhængigheder

Installér afhængigheder med:

```bash
pip install -r src/requirements.txt
```

:key: | **Miljøvariabler**

Zylinc API
- `ZYLINC_URL` URL til API
- `ZYLINC_REALM` Realm til API
- `ZYLINC_CLIENT` Client ID til API
- `ZYLINC_SECRET` Secret til API

Postgres DB
- `QUEUES` Liste med tabel navne på Jobcenter køer fra Postgres DB'en
- `BYGGESAGER_POSTGRES_DB_USER` Brugernavn til Zylinc Postgres DB
- `ZYLINC_POSTGRES_DB_PASS` Adgangskode til Zylinc Postgres DB
- `ZYLINC_POSTGRES_DB_HOST` Hostname til Zylinc Postgres DB
- `ZYLINC_POSTGRES_DB_DATABASE` Databasenavn til Zylinc Postgres DB
- `ZYLINC_POSTGRES_DB_PORT` Portnummer til Zylinc Postgres DB

