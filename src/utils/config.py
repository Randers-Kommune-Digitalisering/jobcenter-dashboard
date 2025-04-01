import os
from dotenv import load_dotenv


# loads .env file, will not overide already set enviroment variables (will do nothing when testing, building and deploying)
load_dotenv()


DEBUG = os.getenv('DEBUG', 'False') in ['True', 'true']
PORT = os.getenv('PORT', '8080')
POD_NAME = os.getenv('POD_NAME', 'pod_name_not_set')

ZYLINC_POSTGRES_DB_HOST = os.getenv("ZYLINC_POSTGRES_DB_HOST")
ZYLINC_POSTGRES_DB_USER = os.getenv("ZYLINC_POSTGRES_DB_USER")
ZYLINC_POSTGRES_DB_PASS = os.getenv("ZYLINC_POSTGRES_DB_PASS")
ZYLINC_POSTGRES_DB_DATABASE = os.getenv("ZYLINC_POSTGRES_DB_DATABASE")
ZYLINC_POSTGRES_DB_PORT = os.getenv("ZYLINC_POSTGRES_DB_PORT")
QUEUES = ['Jobcenter_Jobservice_7733', 'Jobcenter_Fleksgruppen_7734', 'Jobcenter_Jobogtilknytning_7732', 'Jobcenter_Team integration_7738']
ZYLINC_URL = os.environ["ZYLINC_URL"].strip()
ZYLINC_REALM = os.environ["ZYLINC_REALM"].strip()
ZYLINC_CLIENT = os.environ["ZYLINC_CLIENT"].strip()
ZYLINC_SECRET = os.environ["ZYLINC_SECRET"].strip()
