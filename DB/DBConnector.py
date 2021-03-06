"""
    Copyright (C) 2022, Patrick Bleeker
    This program comes with ABSOLUTELY NO WARRANTY;
    See full notice at Main.py
"""

import pymongo.database
from pymongo import MongoClient
from DB import DBExceptions


class DBConnector:
    def __init__(self):
        """
        Can connect to a MongoDB Server by calling the connect() function.\n
        Provides CRUD operations
        """
        self.client = None
        self.db = None
        self.list_dbs = []
        self.list_collections = []
        self.types = {}

    def close(self) -> None:
        """
        Closes connection if one exists\n
        :raises Exception: Exception thrown by pymongo close()
        """
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                raise

    def get_db(self) -> pymongo.database.Database:
        """
        Returns the current Database\n
        :return: current database as Object
        """
        return self.db

    def get_types(self) -> dict:
        """
        Returns a nested dict with the current DB's collection and it's fields with corresponding types\n
        :return: dict with the current DB's collection and it's fields with corresponding types
        """
        self.update_types()
        return self.types

    def get_client(self) -> pymongo.mongo_client.MongoClient:
        """
        :return: current client as Object
        """
        return self.client

    def get_list_dbs(self) -> list:
        """
        Returns list of all available databases
        :return: list of all available databases
        """
        return self.list_dbs

    def get_list_collections(self) -> list:
        """
        Returns a list of all collections in the current database\n
        :return: list of all collections in the current database
        """
        return self.db.list_collection_names()

    def get_collection(self, collection: str) -> pymongo.collection.Collection:
        """
        Returns the specified collection as an object\n
        :param collection: name of the collection
        :return: specified collection as Object
        """
        return self.db[collection]

    def get_collection_entries(self, collection: str, distinct: bool = False) -> pymongo.cursor.Cursor:
        """
        find all entries in the specified collection\n
        equivalent to find() with no query and no projection\n
        :param collection: name of the collection to search through
        :param distinct: specify if just one result should be shown
        :return: cursor to the search result as object
        :raises Exception: Exception thrown by pymongo find()
        """
        try:
            if distinct:
                return self.db[collection].find_one()
            return self.db[collection].find()
        except Exception:
            raise

    def connect(self, db_uri: str) -> None:
        """
        Connects to a Database with given URI\n
        Closes old connection, if there was one\n
        :param db_uri: URI to your MongoDB Server - https://docs.mongodb.com/manual/reference/connection-string/
        :raises DBExceptions.ConnectionFailure: if connection can't be established
        """
        try:
            if self.client is not None:
                self.client.close()
            self.client = MongoClient(f"{db_uri}")
            self.list_dbs = self.client.list_database_names()
        except Exception as e:
            raise DBExceptions.ConnectionFailure(e)

    def insert(self, collection: str, query_list: dict) -> str:
        """
        Equivalent to the MomgoDB insertMany() function\n
        :param collection: String of the collection to insert in
        :param query_list: List with dicts of statements. Same syntax as the MongoDB equivalent
        :return: inserted _id fields
        :raises Exception: Exception thrown by pymongo insert_many()
        """
        try:
            ret = self.db[collection].insert_many(query_list)
        except Exception:
            raise
        return ret.inserted_ids

    def insert_one(self, collection: str, query: dict) -> str:
        """
        Equivalent to the MomgoDB insertOne() function\n
        :param collection: String of the collection to insert in
        :param query: Dict of statements. Same syntax as the MongoDB equivalent
        :return: inserted _id field
        :raises Exception: Exception thrown by pymongo insert_one()
        """
        try:
            ret = self.db[collection].insert_one(query)
        except Exception:
            raise
        return ret.inserted_id

    def find(self, collection: str, query: dict, projection: dict = None) -> list:
        """
        Equivalent to the MongoDB find() function\n
        :param collection: String of the collection to search in
        :param query: Dict of statements. Same syntax as the MongoDB equivalent
        :param projection: Dict of projections - inclusion OR exclusion only - only _id might be ex- and/or included
        :return: list of results - each result is a dict
        :raises Exception: Exception thrown by pymongo find()
        """
        ret = []
        if projection is None:
            projection = {}
        try:
            result = self.db[collection].find(query, projection)
        except Exception:
            raise
        if result is None:
            return ret
        for res in result:
            ret.append(res)
        return ret

    def find_one(self, collection: str, query: dict, projection: dict = None) -> list:
        """
        Equivalent to the MongoDB findOne() function\n
        :param collection: String of the collection to search in
        :param query: Dict of statements. Same syntax as the MongoDB equivalent
        :param projection: Dict of projections - inclusion OR exclusion only - only _id might be ex- and/or included
        :return: list containing first found entry as dict
        :raises Exception: Exception thrown by pymongo find_one()
        """
        ret = []
        if projection is None:
            projection = {}
        try:
            result = self.db[collection].find_one(query, projection)
        except Exception:
            raise
        if result is None:
            return ret
        for res in result:
            ret.append(res)
        return ret

    def update(self, collection: str, query: dict, updates: dict) -> int:
        """
        Equivalent to the MomgoDB updateMany() function\n
        :param collection: String of the collection to update in
        :param query: Dict of statements. Same syntax as the MongoDB equivalent
        :param updates: Dict of updates. Same syntax as the MongoDB equivalent
        :return: amount of updated records
        :raises Exception: Exception thrown by pymongo update_many()
        """
        try:
            result = self.db[collection].update_many(query, updates)
        except Exception:
            raise
        return result.modified_count

    def update_one(self, collection: str, query: dict, updates: dict) -> int:
        """
        Equivalent to the MomgoDB updateOne() function\n
        :param collection: String of the collection to update in
        :param query: Dict of statements. Same syntax as the MongoDB equivalent
        :param updates:
        :return: amount of updated records
        :raises Exception: Exception thrown by pymongo update_one()
        """
        try:
            result = self.db[collection].update_one(query, updates)
        except Exception:
            raise
        return result.modified_count

    def delete(self, collection: str, query: dict) -> int:
        """
        Equivalent to the MongoDB deleteMany() function\n
        :param collection: String of the collection to delete in
        :param query: Dict of statements. Same syntax as the MongoDB equivalent
        :return: amount of deleted records
        :raises Exception: Exception thrown by pymongo delete_many()
        """
        try:
            result = self.db[collection].delete_many(query)
        except Exception:
            raise
        return result.deleted_count

    def delete_one(self, collection: str, query: dict) -> int:
        """
        Equivalent to the MongoDB deleteOne() function\n
        :param collection: String of the collection to delete in
        :param query: Dict of statements. Same syntax as the MongoDB equivalent
        :return: amount of deleted records
        :raises Exception: Exception thrown by pymongo delete_one()
        """
        try:
            result = self.db[collection].delete_one(query)
        except Exception:
            raise
        return result.deleted_count

    def drop_collection(self, collection: str) -> bool:
        """
        Drops the specified collection
        :param collection: name of collection to be dropped
        :returns: True if successfully dropped, else False
        :raises Exception: Exception thrown by pymongo drop()
        """
        try:
            return self.db[collection].drop()
        except Exception:
            raise

    def check_connection(self) -> None:
        """
        :raises DBExceptions.ConnectionFailure: if the connection does not exist
        """
        try:
            self.client.list_database_names()
        except Exception as e:
            raise DBExceptions.ConnectionFailure(e)

    def set_db(self, db: str) -> None:
        """
        Sets the specified database as the current one\n
        :param db: name of database to be set
        :raises DBExceptions.ConnectionFailure: if no connection is established
        """
        try:
            self.db = self.client[db]
        except Exception as e:
            raise DBExceptions.ConnectionFailure(e)

    def update_types(self) -> None:
        """
        Re-evaluates types for every field in every collection for the current database\n
        """
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
                        entries = self.__rec_dict_search(doc[key])
                        for entry in entries:
                            self.types[f"{collection}"][f"{key}.{entry}"] = f"{entries[entry]}"

    def __rec_dict_search(self, doc: dict, init_string: str = "", res: dict = None) -> dict:
        """
        Recursively search through a document to find keys that have dicts as their value\n
        :param doc: document to search through
        :param init_string: string to append to - Default is empty string
        :param res: dict to add results to - Default is None, will create an empty dict
        :return: dict of all fields in the document as keys and it's corresponding type as value
        """
        if res is None:
            res = {}
        for key, value in doc.items():
            if isinstance(value, dict):
                tmp = init_string
                res[init_string + key] = type(value).__name__
                init_string = init_string + key + "."
                self.__rec_dict_search(value, init_string, res)
                init_string = tmp
            else:
                res[init_string + key] = type(value).__name__
        return res
