from pymongo import MongoClient
import DBExceptions


class DBConnector:
    def __init__(self):
        self.client = None
        self.db = None
        self.list_dbs = []
        self.list_collections = []
        self.types = {}

    def close(self):
        if self.client is not None:
            self.client.close()

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

    def get_collection(self, collection):
        return self.db[collection]

    def get_collection_entries(self, collection, distinct=False):
        if distinct:
            return self.db[collection].find_one()
        return self.db[collection].find()

    def get_dict_entries(self, collection, key):
        return self.db[collection].find_one({}, {key: 1})[key]

    def connect(self, db_uri):
        try:
            if self.client is not None:
                self.client.close()
            self.client = MongoClient(f"{db_uri}")
            self.list_dbs = self.client.list_database_names()
        except Exception as e:
            raise DBExceptions.ConnectionFailure(e)

    def find(self, collection, filter_string, projection):
        ret = []
        try:
            result = self.db[collection].find(filter_string, projection)
            for x in result:
                ret.append(x)
        except Exception as e:
            print(e)
        return ret

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
        # DEBUG
        # doc = self.db["TestColl"].find_one({},{"_id": 0})
        # for x in doc:
        #     #print(x, doc[x])
        #     print("result", self.rec_dict_search(doc))
        self.types = {}
        for collection in self.db.list_collection_names():
            # init each new dict with collection name
            self.types[f"{collection}"] = {}
            doc = self.db[collection].find_one()
            # fill new dict with field name and type of field as string
            if doc is not None:
                for key in doc:
                    # doc[key] is the actual field in the document, key is just the name
                    self.types[f"{collection}"][f"{key}"] = f"{type(doc[key]).__name__}"
                    # if key is a dict: add sub-items to self.types with dot Notation
                    if isinstance(doc[key], dict):
                        entries = self.rec_dict_search(doc[key])
                        # entries = self.get_dict_entries(collection, key)
                        for entry in entries:
                            self.types[f"{collection}"][f"{key}.{entry}"] = f"{entries[entry]}"

    def rec_dict_search(self, doc, init_string="", res=None):
        # unsauber, vielleicht nochmal ueberarbeiten
        if res is None:
            res = {}
        for key, value in doc.items():
            if isinstance(value, dict):
                tmp = init_string
                res[init_string + key] = type(value).__name__
                init_string = init_string + key + "."
                self.rec_dict_search(value, init_string, res)
                init_string = tmp
            else:
                res[init_string + key] = type(value).__name__
        return res
