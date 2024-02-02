from sqlalchemy import create_engine, select, insert, MetaData, Table, Column, Integer, VARCHAR
import os
from dotenv import load_dotenv

load_dotenv()

db_connection_string = os.environ.get('DB_CONNECTION_STRING')

class UserDatabase:
    def __init__(self):
        self.engine = create_engine(
            db_connection_string,
            connect_args={
                "ssl": {
                    "ssl_ca": "/etc/ssl/cert.pem"
                }
            }
        )

        self.metadata = MetaData()

        self.users_table = Table(
            'users',
            self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('name', VARCHAR(250), nullable=False),
            Column('email', VARCHAR(250), nullable=False),
            Column('password', VARCHAR(500), nullable=False),
        )

    def add_users_to_db(self, data):
        try:
            with self.engine.connect() as conn:
                query = insert(self.users_table).values(
                    name=data['name'],
                    email=data['email'],
                    password=data['password']
                )
                conn.execute(query)
        except Exception as e:
            print(f"Error occurred while adding user to the database: {e}")

    def check_user_exists(self, email):
        with self.engine.connect() as conn:
            query = select(self.users_table.c.id).where(self.users_table.c.email == email)
            result = conn.execute(query)
            user_exists = result.fetchone()
            return user_exists

    def fetch_user_details(self, email, password):
        with self.engine.connect() as conn:
            query = select(self.users_table.c.id, self.users_table.c.name).where(
                self.users_table.c.email == email, self.users_table.c.password == password
            )
            result = conn.execute(query)
            user = result.fetchone()
            return user
