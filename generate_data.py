import mysql.connector
from faker import Faker
import setup_environment as setup

db = mysql.connector.connect(
    host="localhost",
    user=setup.MYSQL_USER,
    password=setup.MYSQL_ROOT_PASSWORD,
    database=setup.MYSQL_DB,
    port=3306
)

cursor = db.cursor()
fake = Faker()

def generate_data(num_records):

    cursor.execute("SELECT COUNT(*) FROM users;")
    count_before = cursor.fetchone()[0]
    print("Records count before:", count_before)

    for _ in range(num_records):
        name = fake.name()
        email = fake.email()
        address = fake.address()
        phone = fake.phone_number()[:20]

        query = "INSERT INTO users (name, email, address, phone) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (name, email, address, phone))

    db.commit()

    cursor.execute("SELECT COUNT(*) FROM users;")
    count_after = cursor.fetchone()[0]
    print("Records count after:", count_after)

if __name__ == "__main__":
    db, cursor = setup.wait_for_mysql()
    if not db:
        print("MySQL database not found. Make sure to run setup_environment.py first.")
        exit()

    generate_data(100)

    cursor.close()
    db.close()

