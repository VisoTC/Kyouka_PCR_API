import os

REDIS_URL = "redis://{host}:{port}/{db}".format(
    host=os.getenv('ENV_REDIS_HOST') if os.getenv(
        'ENV_REDIS_HOST') != None else "127.0.0.1",
    port=os.getenv('ENV_REDIS_PORT') if os.getenv(
        'ENV_REDIS_PORT') != None else "6379",
    db=os.getenv('ENV_REDIS_DB') if os.getenv('ENV_REDIS_DB') != None else "0")

MYSQL_CONNENT = {
    'database': os.getenv('ENV_MYSQL_DATABASE') if os.getenv(
        'ENV_MYSQL_DATABASE') != None else "pcr",
    'host': os.getenv('ENV_MYSQL_HOST') if os.getenv(
        'ENV_MYSQL_HOST') != None else '127.0.0.1',
    'port': os.getenv('ENV_MYSQL_PORT') if os.getenv(
        'ENV_MYSQL_PORT') != None else 3306,
    'user': os.getenv('ENV_MYSQL_USER') if os.getenv(
        'ENV_MYSQL_USER') != None else 'root',
    'passwd': os.getenv('ENV_MYSQL_PASSWD') if os.getenv(
        'ENV_MYSQL_PASSWD') != None else '123'
}

HTTP_HOST = os.getenv('ENV_HTTP_HOST') if os.getenv(
    'ENV_HTTP_HOST') != None else "127.0.0.1"
HTTP_PORT = os.getenv('ENV_HTTP_PORT') if os.getenv(
    'ENV_HTTP_PORT') != None else "8000"
