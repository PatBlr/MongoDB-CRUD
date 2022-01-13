from pymongo import MongoClient
import DBExceptions


class DBConnector:
    def __init__(self):
        self.client = None
        self.db = None
        self.list_dbs = []
        self.list_collections = []
        self.current_collection = None
        self.types = {}

    def get_db(self):
        return self.db

    def get_types(self):
        return self.types

    def get_client(self):
        return self.client

    def get_list_dbs(self):
        return self.list_dbs

    def get_list_collections(self):
        return self.list_collections

    def get_current_collection(self):
        return self.current_collection

    def get_collection(self, collection):
        return self.db[collection]

    def get_collection_entries(self, collection, distinct=False):
        if distinct:
            return self.db[collection].find_one()
        return self.db[collection].find()

    def connect(self, db_uri):
        try:
            if self.client is not None:
                self.client.close()
            self.client = MongoClient(f"{db_uri}")
            self.list_dbs = self.client.list_database_names()
        except Exception as e:
            raise DBExceptions.ConnectionFailure(e)

    def check_connection(self):
        try:
            self.client.list_database_names()
        except Exception as e:
            raise DBExceptions.ConnectionFailure(e)

    def set_db(self, db):
        try:
            self.db = self.client[db]
            self.list_collections = self.db.list_collection_names()
        except Exception as e:
            raise DBExceptions.ConnectionFailure(e)

    def update_types(self):
        self.types = {}
        for collection in self.db.list_collection_names():
            pass
            # init each new dict with collection name
            self.types[f"{collection}"] = {}
            doc = self.db[collection].find_one()
            if doc is not None:
                for key in doc:
                    # fill new dict with field name and type of field as string
                    # doc[key] is the actual field in the document, key is just the name
                    self.types[f"{collection}"][f"{key}"] = f"{type(doc[key]).__name__}"

