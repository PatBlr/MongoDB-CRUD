"""
    Copyright (C) 2022, Patrick Bleeker
    This program comes with ABSOLUTELY NO WARRANTY;
    See full notice at Main.py
"""

import json
from collections import defaultdict
from datetime import date, datetime


class QueryGenerator:

    def __init__(self, statements: dict) -> None:
        """
        Resolves a dict of statements to a query, usable by the mongosh, a normal string representation of this query
        and a prettified (indented) version of this string\n
        :param statements: dict of statements -
            keys MUST be named statement1 to statementN,
            values MUST be dict containing following keys:
            "field" (e.g. _id),
            "option" (e.g. equals, does not equal, etc...) and
            "text" (compare string)
            example: {statement1: {"field": "_id", "option": "equals", "text": "01"}}
            provided options are: equals, does not equal, grater than, less than, greater or equal, less or equal,
            in, not in, starts with, ends with, contains
        """
        self.options = {
                # resolving table
                # uses string formatting (str.format(argument=...)) to replace {argument} with text contents
                "equals": {"name": "$eq", "argument": "{argument}"},
                "does not equal": {"name": "$ne", "argument": "{argument}"},
                "greater than": {"name": "$gt", "argument": "{argument}"},
                "less than": {"name": "$lt", "argument": "{argument}"},
                "greater or equal": {"name": "$gte", "argument": "{argument}"},
                "less or equal": {"name": "$lte", "argument": "{argument}"},
                "in": {"name": "$in", "argument": "{argument}"},
                "not in": {"name": "$nin", "argument": "{argument}"},
                "starts with": {"name": "$regex", "argument": "/^{argument}/", "options": "m"},
                "ends with": {"name": "$regex", "argument": "/{argument}$/", "options": "m"},
                "contains": {"name": "$regex", "argument": "/{argument}/", "options": ""}
            }
        self.statements = statements
        self.query = {}
        self.query_string = ""
        self.query_string_pretty = ""
        self.__generate()

    def get_query(self) -> dict:
        """
        Returns the generated query
        :return: generated query as dict compatible with pymongo
        """
        return self.query

    def get_query_string(self) -> str:
        """
        Returns the generated string representation of the query
        :return: generated query as string
        """
        return self.query_string

    def get_query_string_pretty(self) -> str:
        """
        Returns the generated and indented representation of the query
        :return: generated query as indented string
        """
        return self.query_string_pretty

    def __generate(self) -> None:
        if len(self.statements) > 1:
            ands = defaultdict(dict)  # dict of dict
            ors = defaultdict(dict)  # dict
            and_statements = []
            or_statements = []
            self.__link_ands(ands)
            found = False
            # searches through all entries in ands to look if statement{i} is in ands
            # if it's not -> must be an or statement so append it to or_statements
            for i in range(1, len(self.statements)+1):
                for liste in ands.values():
                    if f"statement{i}" in liste:
                        found = True
                if not found:
                    ors[f"statement{i}"] = self.statements[f"statement{i}"]
                found = False
            for statements in ands.values():
                and_statements.append(self.__generate_and_statement(statements))
            for statement in ors.values():
                or_statements.append(self.__resolve_statement(statement))
            query_string = self.__generate_query(or_statements, and_statements)
        else:
            query_string = self.__resolve_statement(self.statements["statement1"])
        self.__add_returns(query_string)

    def __link_ands(self, ands: dict, i: int = 1, j: int = 1) -> None:
        # and is stronger than or -> bind the ands and add them to a dict
        if i < len(self.statements):
            if self.statements[f"statement{i+1}"]["clause"] == "and":
                if self.statements[f"statement{i}"]["clause"] != "and":
                    ands[j][f"statement{i}"] = self.statements[f"statement{i}"]
                ands[j][f"statement{i+1}"] = self.statements[f"statement{i+1}"]
                i = i + 1
            else:
                if self.statements[f"statement{i}"]["clause"] == "and":
                    j = j + 1
                i = i + 1
            self.__link_ands(ands, i, j)

    def __resolve_statement(self, statement: dict) -> str:
        try:
            option = self.__resolve_option(statement["option"])
            argument = self.__resolve_argument(statement["option"], statement["text"])
            query = self.__generate_string(statement, option, argument)
            return query
        except Exception as e:
            print(e)

    def __generate_string(self, statement: dict, option: str, argument: str) -> str:
        query = f"{{'{statement['field']}': {{'{option}': {argument}}}}}"
        return query

    def __generate_and_statement(self, statements: dict):
        string = ""
        i = 1
        for statement in statements.values():
            string += self.__resolve_statement(statement)
            if i < len(statements):
                string += ", "
            i += 1
        query = f'"$and": [{string}]'
        return query

    def __generate_query(self, or_statements, and_statements) -> str:
        string = ""
        if len(or_statements) > 0:
            for i, statement in enumerate(or_statements):
                string += statement
                if i < len(or_statements) - 1:
                    string += ", "
            if len(and_statements) > 0:
                string += ", "
        if len(and_statements) > 0:
            for i, statement in enumerate(and_statements):
                if len(or_statements) > 0:
                    string += f"{{{statement}}}"
                else:
                    string += f"{statement}"
                if i < len(and_statements) - 1:
                    string += ", "
        if len(or_statements) > 0:
            query = f'{{"$or": [{string}]}}'
        else:
            query = f"{{{string}}}"
        return query

    def __add_returns(self, query_string: str) -> None:
        query_string = query_string.replace("'", '"')
        self.query = query_string
        self.query_string = query_string
        self.query_string_pretty = self.prettify(query_string)
        query_string = json.loads(query_string.replace("'", '"'))
        # a bit of cheating here, json_util can't resolve regex /.../x, so "/.../x" need it's quotes to be removed
        occ = self.__deep_search_dict(query_string, "$regex")
        for value in occ:
            self.query = self.__remove_regex(self.query, value)
            self.query_string = self.__tidy_up_regex(self.query_string, value)
            self.query_string_pretty = self.__tidy_up_regex(self.query_string_pretty, value)
        self.query = json.loads(self.query)

    def __deep_search_dict(self, dic: dict, searchkey: str, occurrences: list = None) -> list:
        if occurrences is None:
            occurrences = []
        else:
            occurrences = occurrences
        for key, value in dic.items():
            if isinstance(value, dict):
                self.__deep_search_dict(value, searchkey, occurrences)
            elif isinstance(value, list):
                for x in value:
                    self.__deep_search_dict(x, searchkey, occurrences)
            else:
                if key == searchkey:
                    occurrences.append(value)
        return occurrences

    def __tidy_up_regex(self, string: str, text: str) -> str:
        # replaces the '' around any string
        # meant to remove '' around regex inside of statement
        string = string.replace(f"'{text}'", text)
        string = string.replace(f'"{text}"', text)
        return string

    def __remove_regex(self, string: str, text: str) -> str:
        # removes the JS regex indicators // and the option from a string
        string = string.replace(f"{text}", text.replace("/m", "").replace("/", ""))
        string = string.replace(f'"{text}"', text)
        return string

    def __resolve_clause(self, clause: str) -> str:
        if clause in ["and", "or"]:
            clause = "$and" if clause == "and" else "$or"
            return clause

    def __resolve_option(self, option: str) -> str:
        option = self.options[option]["name"]
        return option

    def __resolve_argument(self, argument: str, text: str) -> str:
        argument = self.options[argument]["argument"].format(argument=text)
        # if the argument is not serializable by json, enclose it in quotes
        try:
            json.loads(argument)
        except json.JSONDecodeError:
            argument = f"'{argument}'"
        return argument

    def prettify(self, statement, sort_keys: bool = False) -> str:
        """
        Will indent a string or a dict if it's json serializable\n
        Will raise Exception if either not a dict or a string or if the statement can't be serialized\n
        :param statement: either dict or string to indent
        :param sort_keys: bool if the keys inside the string or dict should be sorted by json
        :return: indented string
        """
        if not isinstance(statement, str) and not isinstance(statement, dict):
            raise ValueError(f"Expected str or dict, received {type(statement)}")
        try:
            if isinstance(statement, str):
                statement = statement.replace("'", '"')
                statement = json.loads(statement)
            statement = f"{json.dumps(statement, indent=4, sort_keys=sort_keys, default=self.__json_serial)}"
            return statement
        except Exception:
            raise

    def __json_serial(self, obj: object) -> str:
        # source: https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))
