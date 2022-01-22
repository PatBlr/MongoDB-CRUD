from bson import json_util
import json
from collections import defaultdict
import DBExceptions


class QueryGenerator:

    def __init__(self, statements, types, projections=None):
        self.statements = statements
        self.types = types
        if projections is not None:
            self.projection = self.__filter_projection(projections)
        else:
            self.projection = {}

        self.options = {
                # resolving table
                # uses string formatting (str.format(argument=...)) to replace {argument} with text contents
                "does not equal": {"name": "$ne", "argument": "{argument}"},
                "equals": {"name": "$eq", "argument": "{argument}"},
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
        self.query_string = ""
        self.query_string_pretty = ""
        self.query = ""
        self.__generate()

    def get_query(self):
        return self.query

    def get_query_string(self):
        return self.query_string

    def get_query_string_pretty(self):
        return self.query_string_pretty

    def get_projection(self):
        return self.projection

    def __generate(self):
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

    def __link_ands(self, ands, i=1, j=1):
        # and is stronger than or -> bind the ands and add them to a dict
        try:
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
        except Exception as e:
            print(e)

    def __resolve_statement(self, statement):
        try:
            option = self.__resolve_option(statement["option"])
            argument = self.__resolve_argument(statement["option"], statement["text"])
            query = self.__generate_string(statement, option, argument)
            return query
        except Exception as e:
            print(e)

    def __generate_string(self, statement, option, argument):
        query = f"{{'{statement['field']}': {{'{option}': {argument}}}}}"
        return query

    def __generate_and_statement(self, statements):
        string = ""
        i = 1
        for statement in statements.values():
            string += self.__resolve_statement(statement)
            if i < len(statements):
                string += ", "
            i += 1
        query = f'"$and": [{string}]'
        return query

    def __generate_query(self, or_statements, and_statements):
        string = ""
        i = 1
        if len(or_statements) > 0:
            for statement in or_statements:
                string += statement
                if i < len(or_statements):
                    string += ", "
                i += 1
            if len(and_statements) > 0:
                string += ", "
        i = 1
        if len(and_statements) > 0:
            for statement in and_statements:
                if len(or_statements) > 0:
                    string += f"{{{statement}}}"
                else:
                    string += f"{statement}"
                if i < len(and_statements):
                    string += ", "
                i += 1

        if len(or_statements) > 0:
            query = f'{{"$or": [{string}]}}'
        else:
            query = f"{{{string}}}"

        return query

    def __add_returns(self, query_string):
        self.query = query_string
        if self.projection != {}:
            self.query_string = f"{query_string}, {self.projection}"
        else:
            self.query_string = f"{query_string}"
        projection = json.loads(str(self.projection).replace("'", '"'))
        print("query_string", query_string)
        try:
            query_string = query_string.replace("'", '"')
            query_string = json.loads(query_string.replace("'", '"'))
        except json.decoder.JSONDecodeError as e:
            print(e, type(e))
        print("query_string_after", query_string)
        if self.projection != {}:
            print("pretty", self.query_string_pretty)
            self.query_string_pretty = f"{json.dumps(query_string, indent=4, sort_keys=False)}, " \
                                       f"{json.dumps(projection, indent=4, sort_keys=False)}"
            print("pretty_after", self.query_string_pretty)
        else:
            self.query_string_pretty = f"{json.dumps(query_string, indent=4, sort_keys=False)}"
        # a bit of cheating here, json_util can't resolve regex /.../x, so "/.../x" need it's quotes to be removed
        occ = self.__deep_search_dict(query_string, "$regex")
        for value in occ:
            self.query_string = self.__tidy_up_regex(self.query_string, value)
            self.query_string_pretty = self.__tidy_up_regex(self.query_string_pretty, value)
            self.query = self.__remove_regex(self.query, value)

    def __deep_search_dict(self, dic, searchkey, occurrences=None):
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

    def __tidy_up_regex(self, string, text):
        # replaces the '' around any string
        # meant to remove '' around regex inside of statement
        string = string.replace(f"'{text}'", text)
        string = string.replace(f'"{text}"', text)
        return string

    def __remove_regex(self, string, text):
        # removes the JS regex indicators // and the option from a string
        string = string.replace(f"{text}", text.replace("/m", "").replace("/", ""))
        string = string.replace(f'"{text}"', text)
        return string

    def __filter_projection(self, projections):
        # cannot do inclusion in exclusion projection and vice versa
        # filter out included projections (key = 1) and append it to the dict
        filtered = {}
        for key, value in projections.items():
            if value == 1 or key == '_id':
                filtered[key.replace("'", '"')] = value
        return filtered

    def __resolve_clause(self, clause):
        if clause in ["and", "or"]:
            clause = "$and" if clause == "and" else "$or"
            return clause

    def __resolve_option(self, option):
        option = self.options[option]["name"]
        return option

    def __resolve_argument(self, argument, text):
        argument = self.options[argument]["argument"].format(argument=text)
        # if the argument is not serializable by json, enclose it in quotes
        try:
            json.loads(argument)
        except json.JSONDecodeError:
            argument = f"'{argument}'"
        return argument
