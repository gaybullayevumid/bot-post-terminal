from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")
ADMINS = env.list("ADMINS")
IP = env.str("IP")

# DB_CONFIG = {
#     'user':'DB_USER',
#     'password': 'DB_PASS',
#     'database': 'DB_NAME',
#     'host': 'DB_HOST',
# }

DB_CONFIG = {
    "dbname": "avtolider",
    "user": "postgres",
    "password": "8505",
    "host": "localhost",
    "port": "5432"
}
