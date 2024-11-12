import docker
import mysql.connector
import psycopg2
from time import sleep, time

client = docker.from_env()

MYSQL_IMAGE = "mysql:8.4.3"
MYSQL_CONTAINER_NAME = "mysql_container"
MYSQL_ROOT_PASSWORD = "rootpassword"
MYSQL_USER = "mysql_user"
MYSQL_DB = "mysql_db"

POSTGRES_CONTAINER_NAME = "postgres_container"
POSTGRES_IMAGE = "postgres:17.0"
POSTGRES_PASSWORD = "postgres_password"
POSTGRES_USER = "postgres_user"
POSTGRES_DB = "postgres_db"


def get_mysql_container():
    try:
        existing_container = client.containers.get(MYSQL_CONTAINER_NAME)
        if existing_container.status == "running":
            return existing_container
        else:
            existing_container.start()
    except docker.errors.NotFound:
        pass
    existing_container = client.containers.run(
        MYSQL_IMAGE,
        name=MYSQL_CONTAINER_NAME,
        environment={
            "MYSQL_ROOT_PASSWORD": MYSQL_ROOT_PASSWORD,
            "MYSQL_DATABASE": MYSQL_DB,
            "MYSQL_USER": MYSQL_USER,
            "MYSQL_PASSWORD": MYSQL_ROOT_PASSWORD,
        },
        ports={"3306/tcp": 3306},
        detach=True,
    )
    return existing_container


def create_mysql_container():
    try:
        existing_container = client.containers.get(MYSQL_CONTAINER_NAME)
        existing_container.remove(force=True)
    except docker.errors.NotFound:
        pass

    return get_mysql_container()


def get_postgres_container():
    try:
        existing_container = client.containers.get(POSTGRES_CONTAINER_NAME)
        if existing_container.status == "running":
            return existing_container
        else:
            existing_container.start()
    except docker.errors.NotFound:
        pass
        existing_container = client.containers.run(
            POSTGRES_IMAGE,
            name=POSTGRES_CONTAINER_NAME,
            environment={
                "POSTGRES_PASSWORD": POSTGRES_PASSWORD,
                "POSTGRES_DATABASE": POSTGRES_DB,
                "POSTGRES_USER": POSTGRES_USER,
            },
            ports={"5432/tcp": 5433},
            detach=True,
        )
        return existing_container


def create_postgres_container():
    try:
        existing_container = client.containers.get(POSTGRES_CONTAINER_NAME)
        existing_container.remove(force=True)
    except docker.errors.NotFound:
        pass
    return get_postgres_container()


def create_mysql_table():
    db = mysql.connector.connect(
        host="localhost",
        user=MYSQL_USER,
        password=MYSQL_ROOT_PASSWORD,
        database=MYSQL_DB,
        port=3306,
    )
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100),
            address VARCHAR(255),
            phone VARCHAR(20)
        );
    """)
    db.commit()
    cursor.close()
    db.close()


def create_postgres_db():
    conn = psycopg2.connect(
        host="localhost", user=POSTGRES_USER, password=POSTGRES_PASSWORD, port=5433
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE {POSTGRES_DB} WITH OWNER = {POSTGRES_USER};")
    cursor.close()
    conn.close()


def wait_for_mysql(timeout=120):
    print("Waiting for MySQL...")
    start_time = int(time())
    while start_time + timeout > int(time()):
        try:
            db = mysql.connector.connect(
                host="localhost",
                user=MYSQL_USER,
                password=MYSQL_ROOT_PASSWORD,
                database=MYSQL_DB,
                port=3306,
            )
            cursor = db.cursor()
            cursor.execute(f"SELECT 1;")
            cursor.reset()
            print("Connection to MySQL successful.")
            return (db, cursor)
        except mysql.connector.Error:
            sleep(1)


def wait_for_postgres(timeout=120):
    print("Waiting for PostgreSQL container to be ready...")
    start_time = int(time())
    while start_time + timeout > int(time()):
        try:
            db = psycopg2.connect(
                host="localhost",
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                database=POSTGRES_DB,
                port=5433,
            )
            cursor = db.cursor()
            cursor.execute(f"SELECT 1;")
            print("Connection to PostgreSQL successful.")
            return (db, cursor)
        except psycopg2.OperationalError as e:
            if f'database "{POSTGRES_DB}" does not exist' in str(e):
                create_postgres_db()
        except psycopg2.Error as e:
            print(f"{e}")
            sleep(1)


if __name__ == "__main__":
    create_mysql_container()
    create_postgres_container()

    wait_for_mysql()
    wait_for_postgres()

    create_mysql_table()

