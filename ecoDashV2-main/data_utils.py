import pandas as pd
from google.cloud.sql.connector import Connector
import pymysql
import sqlalchemy
from datetime import datetime
from supabase import Client, create_client
from google.cloud import secretmanager

def get_secrets(project_id):
    client = secretmanager.SecretManagerServiceClient()
    catch_secrets = {}
    secret_names = ['supabase_url', 'supabase_key', 'platform_analytics_db_pass',
                    'platform_analytics_db_user', 'platform_analytics_db_name', 'platform_analytics_db_host',
                    'platform_analytics_db_instance_connection_name', 'supa_db_user', 'supa_db_pass', 'supa_host',
                    'supa_db_port', 'supa_db_name']

    for secret in secret_names:
        try:
            name = f"projects/{project_id}/secrets/{secret}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            catch_secrets[secret] = response.payload.data.decode("UTF-8")
        except Exception as e:
            print(f"Error accessing secret {secret}: {e}")

    return catch_secrets


project_id = 'platform-analyti-1683293526087'
secrets = get_secrets(project_id)

supabase: Client = create_client(secrets['supabase_url'], secrets['supabase_key'])

ASSET_COLS = ['platformID', 'name', 'assetSubTypes', 'platformModDate',
              'assetType', 'excludeFromUpdate', 'platformCreatedDate',
              'ecosystem', 'keywords', 'hostRelation', 'claimed', 'email',
              'associatedRelation', 'sponsoredRes', 'dciID', 'keyDCI',
              'activityStatus', 'syncDate']
USER_COLS = ['email', 'user_types', 'ecosystem', 'keywords', 'platformID',
             'platform_created_date', 'platformModDate', 'associated_orgs', 'keyDCI']
SUPA_COLS = {
    'platform_assets': '"name", "assetSubTypes", "platformModDate", "assetType", "excludeFromUpdate", "activityStatus",'
                       '"platformID", "email", "platformCreatedDate", "ecosystem", "keywords", "claimed", "email", '
                       '"dciID", "keyDCI"',
    'platform_users': '"email", "user_types", "ecosystem", "keywords", "platformID", "platform_created_date", '
                      '"platformModDate", "associated_orgs", "keyDCI"',
    'platform_keys': '"platform_id", "type", "ecosystem", "name", "dciID", "platformModDate"'
}

KEY_COLS = ['platform_id', 'type', 'ecosystem', 'name', 'dciID', 'platformModDate']
ACTIVITY_TYPES = ['Viewed', 'Visited', 'Saved']

ASSET_TYPES = ['Organizations', 'Resources', 'Events', 'Jobs', 'News']
KEY_TYPES = ['Audience', 'Scope of Work', 'Compensation', 'Talent Status', 'General Tags', 'Industries',
             'Job Type', 'Location', 'Organization Functions', 'Organization Category', 'Topics', 'Stage',
             'Resource Type', 'Certifications', 'Skills', 'Educational Background', 'Products and Services',
             'Ownership', 'Goals', 'Job Positions', 'Offerings', 'Company Development Phase', 'Individual Functions',
             'Individual Functions', 'Position/Title', 'Primary Licensing/Fund', 'Registration Status', 'Regulatory Class',
             'Specialty/Clinical Indication', 'Target Capital Raise', 'Types of AgBio', 'Types of Animal Healthcare',
             'Types of Combination Products', 'Types of Community Development Orgs', 'Types of Emerging Company Support',
             'Types of Funding Sources', 'Types of Laboratory Testing', 'Types of Life Sciences Tools',
             'Types of Medical Devices', 'Types of Medical Technology', 'Types of Pharmaceutical Therapies',
             'Types of Point of Care Testing', 'Types of Research and Education Institutions',
             'Types of Life Science Companies', 'Types of BioTech Therapeutics and Diagnostics', 'Collecting Area']

DATE_PRESETS = {'Past 7 Days': 7, 'Past 14 Days': 14, 'Past 30 Days': 30, 'Past 60 Days': 60, 'Past 90 Days': 90}
user_color_dict = {'All Users': '#171444', 'Verified User': '#0F0069', 'Admin': '#1D00A5', 'Case Manager': '#3323CC',
                   'Community Admin': '#4D44E3', 'Fellow': '#6760FD', 'Service Provider': '#8582FF','Service provider': '#8582FF',
                   'EcoMap': '#E2DFFF', 'Course Creator': '#C3C0FF'}

asset_color_dict = {'All Assets': '#171444', 'Organization': '#1D00A5', 'Resource': '#4D44E3',
                    'Event': '#8582FF', 'Job': '#C3C0FF', 'News': '#E2DFFF'}


connector = Connector()

def getconn():
    conn = connector.connect(
        secrets['platform_analytics_db_instance_connection_name'],
        "pymysql",
        user=secrets['platform_analytics_db_user'],
        host=secrets['platform_analytics_db_host'],
        password=secrets['platform_analytics_db_pass'],
        db=secrets['platform_analytics_db_name'],
        port='3306',
    )
    return conn


def query_sql(ecosystem: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:

    if not ecosystem or ecosystem == 'None' or ecosystem =='Select Ecosystem':
        return pd.DataFrame()
    pool = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
    )

    with pool.connect() as db_conn:
        results = db_conn.execute(
            sqlalchemy.text("""SELECT ecomapCreated, user, createdDate, dataType, usersTypes, onPage, activityType,
                            pageName, dataObject, platformID  FROM activityFeed WHERE ecosystem LIKE :search_term 
                            AND createdDate BETWEEN :start_date AND :end_date
                            AND activityType IN ('Viewed', 'Visited', 'Saved')
                            AND dataType IN ('Organizations', 'Resources', 'Events', 'Jobs', 'News')"""),
            parameters={"search_term": f"%{ecosystem}%",
                        "start_date": start_date,
                        "end_date": end_date}).fetchall()
        df = pd.DataFrame(results)

    return df


def get_ecosystems():
    pool = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
    )

    with pool.connect() as db_conn:
        results = db_conn.execute(
            sqlalchemy.text("SELECT DISTINCT ecosystem FROM activityFeed")).fetchall()
        df = pd.DataFrame(results)
        
    return df


def create_engine():
    username = secrets['supa_db_user']
    password = secrets['supa_db_pass']
    host = secrets['supa_host']
    port = secrets['supa_db_port']  # PostgreSQL default port is 5432
    database = secrets['supa_db_name']

    return sqlalchemy.create_engine(f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}")


def query_database(engine, query, params=None):
    with engine.connect() as connection:
        try:
            return pd.read_sql_query(query, connection, params=params)
        except Exception as e:
            print(e)
            return pd.DataFrame()
        #return pd.read_sql_query(query, connection, params=params)


def query_supa(ecosystem: str, table) -> pd.DataFrame:
    if not ecosystem or ecosystem == 'None' or ecosystem =='Select Ecosystem':
        return pd.DataFrame()
    data = supabase.table(table).select('*').eq('ecosystem', ecosystem).execute()
    return pd.DataFrame(data.data)

"""
def query_supa(ecosystem: str, table: str) -> pd.DataFrame:
    if not ecosystem or ecosystem == 'None' or ecosystem == 'Select Ecosystem':
        return pd.DataFrame()

    if table not in SUPA_COLS:
        raise ValueError("Invalid table name")

    engine = create_engine()

    sql_query = sqlalchemy.text(f"SELECT {SUPA_COLS[table]} FROM {table} WHERE ecosystem = :searchterm")
    params = {"searchterm": ecosystem}

    try:
        return query_database(engine, sql_query, params)
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()"""


