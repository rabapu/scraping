import pymysql
from config import Config

def get_db_connection():
    return pymysql.connect(**Config.DB_CONFIG)