import mysql.connector

# Connect to MySQL using the 'mysql_native_password' authentication plugin
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="Passw0rd",  # Replace with your actual password
    auth_plugin='mysql_native_password'  # Specify the authentication plugin
)

my_cursor = mydb.cursor()

# Create the database
#my_cursor.execute("CREATE DATABASE our_users")

# List the databases
my_cursor.execute("SHOW DATABASES")
for db in my_cursor:
    print(db)