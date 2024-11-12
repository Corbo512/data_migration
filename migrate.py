import docker
import setup_environment as setup
from time import sleep, time

image = "nmig_image"

client = docker.from_env()


def start_containers():
    mysql_container = setup.get_mysql_container()
    postgresql_container = setup.get_postgres_container()
    try:
        nmig_container = client.containers.get("nmig_container")
        nmig_container.remove(
            force=True
        )
    except docker.errors.NotFound:
        pass
    nmig_container = client.containers.run(
        image=image,
        command=["npm", "start"],
        detach=True,
        name="nmig_container",
    )
    wait_for_migration_to_finish()

    return [mysql_container, postgresql_container, nmig_container]


def clean_up_containers(containers):
    nmig_container = containers[2]

    while True:
        nmig_container.reload()
        if nmig_container.status == "exited":
            break
        sleep(1)

    for container in containers:
        try:
            container.stop()
        except docker.errors.NotFound:
            print(f"Container {container.name} not found")


def wait_for_migration_to_finish(timeout=120):
    print("Waiting for migration to finish...")
    start_time = int(time())

    nmig_container = client.containers.get("nmig_container")
    while start_time + timeout > int(time()):
        nmig_container.reload()
        if nmig_container.status == "exited":
            print("Migration finished")
            return
        sleep(1)


def verify_migration():
    mysql_conn, mysql_cursor = setup.wait_for_mysql()
    postgres_conn, postgres_cursor = setup.wait_for_postgres()
    mysql_cursor.execute("SELECT COUNT(*) FROM users;")
    mysql_count = mysql_cursor.fetchone()[0]

    postgres_cursor.execute("SELECT COUNT(*) FROM users;")
    postgres_count = postgres_cursor.fetchone()[0]

    if mysql_count == postgres_count:
        print("Migration successful.")
        print(f"Records migrated: {mysql_count}")
    else:
        print("Migration error.")
        print(f"MySQL: {mysql_count}, PostgreSQL: {postgres_count}")

    mysql_cursor.close()
    mysql_conn.close()
    postgres_cursor.close()
    postgres_conn.close()


if __name__ == "__main__":
    containers = start_containers()
    verify_migration()
    clean_up_containers(containers)
