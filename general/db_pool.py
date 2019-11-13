from conf.default import DefaultConfig as current_app
import pymysql
from DBUtils.PooledDB import PooledDB

pool = PooledDB(
    creator=pymysql,
    maxconnections=20,
    user=current_app.DB_USER,
    passwd=current_app.DB_PASSWORD,
    db=current_app.DB_NAME,
    charset=current_app.DB_CHARSET,
    port=current_app.DB_PORT or 3306,
    host=current_app.DB_HOST or '127.0.0.1'
)


def select_sql_execute(cursor, sql):
    cursor.execute(sql)
    return cursor.fetchall()


def get_one(cursor, sql, arg):
    cursor.execute(sql, arg)
    return cursor.fetchone()


def insert_sql_execute(cursor, sql, args):
    ret = cursor.execute(sql, args)
    return ret


def delete_sql_execute(cursor, sql, args):
    ret = cursor.execute(sql, args)
    return ret


def update_sql_execute(cursor, sql, args):
    ret = cursor.execute(sql, args)
    return ret


def execute_sql(sql, args):
    connection = pool.connection()
    cursor = connection.cursor()
    ret = None
    try:
        ret = cursor.execute(sql, args)
        connection.commit()
    except Exception:
        connection.rollback()
        connection.commit()
        raise
    finally:
        cursor.close()
        connection.close()
    return ret


def execute_query_sql(sql, args, key=lambda c: c.fetchall()):
    connection = pool.connection()
    cursor = connection.cursor()
    ret = None
    try:
        cursor.execute(sql, args)
        ret = key(cursor)
    finally:
        cursor.close()
        connection.close()
    return ret


def fetchone_dict(sql, args, template_class):
    connection = pool.connection()
    cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
    template = None
    try:
        cursor.execute(sql, args)
        ret = cursor.fetchone()
        if ret:
            template = template_class()
            for k, v in ret.items():
                setattr(template, k, v)
    finally:
        cursor.close()
        connection.close()
    return template


def fetchall_dict(sql, args, template_class):
    connection = pool.connection()
    cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
    template_list = []
    try:
        cursor.execute(sql, args)
        ret = cursor.fetchall()
        for t in ret:
            template = template_class()
            for k, v in t.items():
                setattr(template, k, v)
            template_list.append(template)
    finally:
        cursor.close()
        connection.close()
    return template_list
