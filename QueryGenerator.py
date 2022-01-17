from bson import ObjectId
import DBExceptions


class QueryGenerator:

    def __init__(self, field, field_type, option, text, projection, types):
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
        self.field = field
        self.field_type = field_type
        self.option = option
        self.comp = self.resolve_comp(self.option)
        self.text = text
        self.parsed_text = self.resolve_argument(option, self.text)
        self.argument = ""
        self.projection = projection
        self.inclusion_list = {}
        self.types = types
        try:
            self.resolve_type()
        except DBExceptions.UnexpectedValue as e:
            raise e
        self.filter_projection()

    def generate_string(self):
        # TODO: muuuuch f-string bracket escaping ...
        text = self.text
        if self.comp == "$regex":
            option = self.options[self.option]["options"]
            text = f"/{text}/{option}"
        comp = f"{{{self.comp}: {text}}}"
        filter_query = f"{{'{self.field}': {comp}}}"
        query = f"{filter_query}, {self.inclusion_list}"
        return query

    def generate_query(self):
        # can't return a string... pymongo find only allows dicts or BSON -> return tuple of dicts
        filter_query = {self.field: {self.comp: self.parsed_text}}
        return filter_query, self.inclusion_list

    def filter_projection(self):
        # cannot do inclusion in exclusion projection and vice versa
        for key, value in self.projection.items():
            if value == 1 or key == '_id':
                self.inclusion_list[key] = value

    def resolve_comp(self, comp_string):
        comp = self.options[comp_string]["name"]
        return comp

    def resolve_argument(self, comp_string, text):
        argument = self.options[comp_string]["argument"]
        return argument.format(argument=text)

    def resolve_type(self):
        if self.comp == "$regex":
            # regex only on strings -> don't cast text
            return
        if self.types[self.field] == 'bool':
            if self.text == 'false':
                self.parsed_text = False
            elif self.text == 'true':
                self.parsed_text = True
            else:
                raise DBExceptions.UnexpectedValue(f"Bool {self.text} not defined. Possible entries: [true, false]")
        if self.types[self.field] == 'int':
            try:
                self.parsed_text = int(self.text)
            except ValueError:
                raise DBExceptions.UnexpectedValue("expected int")
        if self.types[self.field] == 'float':
            try:
                self.parsed_text = float(self.text)
            except ValueError:
                raise DBExceptions.UnexpectedValue("expected float")
        if self.types[self.field] == 'ObjectId':
            try:
                self.parsed_text = ObjectId(self.text)
            except ValueError:
                raise DBExceptions.UnexpectedValue("expected ObjectId")
