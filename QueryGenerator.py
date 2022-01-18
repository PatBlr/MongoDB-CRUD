from bson import ObjectId
from collections import defaultdict
import DBExceptions


class QueryGenerator:

    def __init__(self, statements, types, projections):
        self.statements = statements
        self.types = types
        self.projection = self.filter_projection(projections)
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
                "starts with": {"name": "$regex", "argument": "^{argument}", "options": "m"},
                "ends with": {"name": "$regex", "argument": "{argument}$", "options": "m"},
                "contains": {"name": "$regex", "argument": "{argument}", "options": ""}
            }
        self.test()

    def test(self):
        if len(self.statements) > 1:
            ands = defaultdict(dict)  # dict of dict
            ors = defaultdict(dict)  # dict
            and_statements = []
            or_statements = []

            self.rec_test(ands, 1, 1)

            found = False
            for i in range(1, len(self.statements)+1):
                for liste in ands.values():
                    if f"statement{i}" in liste:
                        found = True
                if not found:
                    ors[f"statement{i}"] = self.statements[f"statement{i}"]
                found = False
            for statements in ands.values():
                and_statements.append(self.generate_and_statement(statements))
            for statement in ors.values():
                or_statements.append(self.resolve_statement(statement))

            if len(or_statements) > 0:
                print(self.generate_or_statement(and_statements, or_statements))
            else:
                print(self.generate_and_statement(and_statements))

            # print("ands",ands)
            # print("ors",ors)
            # print("or_statements",or_statements)
            # print("and_statements",and_statements)


                #print(self.generate_and_statement(statements))
        else:
            statement = self.statements["statement1"]
            print(self.resolve_statement(statement))

    def rec_test(self, ands, i, j):
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
                self.rec_test(ands, i, j)
        except Exception as e:
            print(e)

    def resolve_statement(self, statement):
        try:
            option = self.resolve_option(statement["option"])
            parsed_text = self.resolve_type(option, statement["text"], statement["field"])
            argument = self.resolve_argument(statement["option"], statement["text"])

            query = self.generate_string(statement, option, argument)
            return query
        except Exception as e:
            print(e)

    def generate_string(self, statement, option, argument):
        if option == "$regex":
            argument = f"/{argument}/{self.options[statement['option']]['options']}"
        query = f"{{'{statement['field']}': {{'{option}': {argument}}}}}"
        return query

    def generate_or_statement(self, and_statements, or_statements):
        string = ""
        i = 1
        for statement in or_statements:
            string += statement
        for statement in and_statements:
            string += statement
            if i < len(and_statements):
                string += ", "
            i += 1

        query = f"$or: [{string}]"
        return query

    def generate_and_statement(self, statements):
        string = ""
        i = 1
        for statement in statements.values():
            string += self.resolve_statement(statement)
            if i < len(statements):
                string += ","
            i += 1
        query = f"$and: [{string}]"
        return query

    def generate_query(self, and_statements, or_statements):
        pass

    #
    # def generate_query(self):
    #     # can't return a string... pymongo find only allows dicts or BSON -> return tuple of dicts
    #     filter_query = {self.field: {self.comp: self.parsed_text}}
    #     return filter_query, self.inclusion_list
    #

    def filter_projection(self, projections):
        # cannot do inclusion in exclusion projection and vice versa
        filtered = {}
        for key, value in projections.items():
            if value == 1 or key == '_id':
                filtered[key] = value
        return filtered

    def resolve_clause(self, clause):
        if clause in ["and", "or"]:
            clause = "$and" if clause == "and" else "$or"
            return clause

    def resolve_option(self, option):
        option = self.options[option]["name"]
        return option

    def resolve_argument(self, argument, text):
        argument = self.options[argument]["argument"]
        return argument.format(argument=text)

    def resolve_type(self, option, text, field):
        if option == "$regex":
            # regex only on strings -> don't cast text
            return text
        if self.types[field] == 'bool':
            if text == 'false':
                parsed_text = False
            elif text == 'true':
                parsed_text = True
            else:
                raise DBExceptions.UnexpectedValue(f"Bool '{text}' not defined. Possible entries: [true, false]")
            return parsed_text
        if self.types[field] == 'int':
            try:
                parsed_text = int(text)
            except ValueError:
                raise DBExceptions.UnexpectedValue("expected int")
            return parsed_text
        if self.types[field] == 'float':
            try:
                parsed_text = float(text)
            except ValueError:
                raise DBExceptions.UnexpectedValue("expected float")
            return parsed_text
        if self.types[field] == 'ObjectId':
            try:
                parsed_text = ObjectId(text)
            except ValueError:
                raise DBExceptions.UnexpectedValue("expected ObjectId")
            return parsed_text
        return text
