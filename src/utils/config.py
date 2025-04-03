import os
from dotenv import load_dotenv


# loads .env file, will not overide already set enviroment variables (will do nothing when testing, building and deploying)
load_dotenv()


DEBUG = os.getenv('DEBUG', 'False') in ['True', 'true']
PORT = os.getenv('PORT', '8080')
POD_NAME = os.getenv('POD_NAME', 'pod_name_not_set')

# Keycloack Auth
# KEYCLOAK_URL = os.environ["KEYCLOAK_URL"].strip()
# KEYCLOAK_REALM = os.environ["KEYCLOAK_REALM"].strip()
# KEYCLOAK_CLIENT_ID = os.environ["KEYCLOAK_CLIENT_ID"].strip()

ZYLINC_POSTGRES_DB_HOST = os.getenv("ZYLINC_POSTGRES_DB_HOST")
ZYLINC_POSTGRES_DB_USER = os.getenv("ZYLINC_POSTGRES_DB_USER")
ZYLINC_POSTGRES_DB_PASS = os.getenv("ZYLINC_POSTGRES_DB_PASS")
ZYLINC_POSTGRES_DB_DATABASE = os.getenv("ZYLINC_POSTGRES_DB_DATABASE")
ZYLINC_POSTGRES_DB_PORT = os.getenv("ZYLINC_POSTGRES_DB_PORT")

# POSTGRES
POSTGRES_DB_HOST = os.environ.get('POSTGRES_DB_HOST')
POSTGRES_DB_USER = os.environ.get('POSTGRES_DB_USER')
POSTGRES_DB_PASS = os.environ.get('POSTGRES_DB_PASS')
POSTGRES_DB_DATABASE = os.environ.get('POSTGRES_DB_DATABASE')
POSTGRES_DB_PORT = os.environ.get('POSTGRES_DB_PORT')
