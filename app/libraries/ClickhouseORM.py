from infi.clickhouse_orm import Database

from app.setting import CLICKHOUSE_DATABASE_NAME, CLICKHOUSE_HOST, CLICKHOUSE_PORT, \
    CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD


def ClickhouseBase():
    return Database(db_name=f'{CLICKHOUSE_DATABASE_NAME}', db_url=f'http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/',
                    username=f'{CLICKHOUSE_USERNAME}', password=f'{CLICKHOUSE_PASSWORD}')
