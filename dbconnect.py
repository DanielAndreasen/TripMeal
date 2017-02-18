import MySQLdb


def connection():
    conn = MySQLdb.connect(host="localhost",
                           user="root",
                           passwd="gichin124",
                           db="tripmeal")
    c = conn.cursor()
    return c, conn
