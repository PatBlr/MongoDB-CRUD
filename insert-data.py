"""
    Copyright (C) 2022, Patrick Bleeker
    This program comes with ABSOLUTELY NO WARRANTY;
    See full notice at Main.py
"""

import argparse
from sys import exit
import DB.DBExceptions
from DB.DBConnector import DBConnector
import json


# parse command line arguments for file, database name and server address
parser = argparse.ArgumentParser(description='Connect to Database and insert data')
parser.add_argument('-f', '--file',
                    help="Input File location")
parser.add_argument('-d', '--dbname',
                    help="Database Name")
parser.add_argument('-s', '--server',
                    help="Server's address - "
                    "For further help visit https://docs.mongodb.com/manual/reference/connection-string/")

args = parser.parse_args()
insert_file = args.file
server_address = args.server
dbname = args.dbname
# error handling
if insert_file is None or server_address is None or dbname is None:
    print("Please specify every option. For help type -h")
    exit(1)
connector = DBConnector()
# connecting to Database
try:
    connector.connect(server_address)
    connector.set_db(dbname)
    # do not insert if db already exists
    if dbname in connector.get_list_dbs():
        print(f"Database {dbname} already exists. Please choose another Name")
        exit(1)
except DB.DBExceptions.ConnectionFailure as e:
    print(e)
    exit(1)
count = 0
try:
    # read specified file line by line
    # if the line contains an insert-statement split the string to only contain the statement
    # after that parse it to json and insert into database
    with open(insert_file, "r") as file:
        while True:
            line = file.readline()
            if not line:
                break
            if line.find("insert") > -1:
                try:
                    string = line[line.find("(")+1:line.find(")")]
                    collection = line.split(".")[1]
                    count += 1
                    try:
                        parsed = json.loads(string.replace("'", '"'))
                        if "_id" in parsed:
                            print(f"Inserting: {parsed['_id']} into {collection}")
                        else:
                            print(f"Inserting: generated _id into {collection}")
                        connector.insert_one(collection, parsed)
                    except json.decoder.JSONDecodeError:
                        print(f"Could not parse line: {line}"
                              f"Continuing with next line")
                        count -= 1
                except IndexError:
                    print(f"Faulty line found: {line}"
                          f"Continuing with next line")
except EnvironmentError:
    print(f"File {insert_file} cannot be read")
    exit(1)
except Exception as e:
    print(e)
    exit(1)
print(f"Successfully inserted {count} lines.")
