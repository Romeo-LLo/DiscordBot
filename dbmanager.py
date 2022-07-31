import os
from datetime import datetime
from typing import List
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure


class DatabaseManager:
    def __init__(
            self,
            dbname: str
    ):
        """
        Parameters
        ----------
        dbname : Specify the working database.
        """
        self.dbname = dbname
        self.client = self._connect_db()

        # Create database
        if dbname not in self.client.list_database_names():
            print(f'Database {dbname} not exists. Creating a new database for {dbname}')

        self.db = Database(self.client, name=dbname)
        self.game_collection = self.db["game_collection"]
        self.player_collection = self.db["player_collection"]


    def _connect_db(self):
        """
        Connect to MongoDB server.
        Returns
        ----------
        client : Client for a MongoDB instance.
        """
        client = MongoClient(
            host='localhost',
            port=27017,
        )

        # Check connection
        try:
            client.admin.command('ping')  # The ping command is cheap and does not require auth.
        except ConnectionFailure:
            print("Cannot connect to the database.", fb='red')

        return client
    
    def insert_game_document(self, game_document):
        self.game_collection.insert_one(game_document)
        
    def query_game_document(self, game_name):
        filterQ = {"game": game_name}
        projectionQ = {"_id": 0}
        cursor = self.game_collection.find_one(filterQ, projectionQ)

        return cursor
    
    def replace_game_document(self, game_name, game_document):
        filterQ = {"game": game_name}
        self.game_collection.replace_one(filterQ, game_document)
        
    def count_game_collection(self):
        count = self.game_collection.count_documents({})
        return count
    
    def update_player_collection(self):
        # filterQ = {}
        # projectionQ = {'_id': 0, 'player_list': 1}
        # all_player_list = self.game_collection.find(filterQ, projectionQ)
        # duplicate_list = []
        # for player_list in all_player_list:
        #     duplicate_list += player_list
        
        # player_set = set(duplicate_list)
        
        # for player in player_set:
        #     filterQ = {}
        #     projectionQ = {'_id': 0, 'player_list': 1}
    def delete_game_collection(self):
        self.game_collection.drop()
            

        