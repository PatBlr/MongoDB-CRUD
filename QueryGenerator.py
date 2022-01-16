from bson import ObjectId
from datetime import datetime
import DBExceptions


class QueryGenerator:

    def __init__(self, field, field_type, comp, text, projection, types):
        self.field = field
        self.field_type = field_type
        self.comp = comp
        self.text = text
        self.projection = projection
        self.inclusion_list = {}
        self.types = types
        self.resolve_type()
        self.filter_projection()

    def generate_string(self):
        filter_query = {self.field: {self.comp: self.text}}
        query = f"{filter_query}, {self.inclusion_list}"
        return query

    def generate_query(self):
        filter_query = {self.field: {self.comp: self.text}}
        return filter_query, self.inclusion_list

    def filter_projection(self):
        # cannot do inclusion in exclusion projection and vice versa
        for key, value in self.projection.items():
            if value == 1 or key == '_id':
                self.inclusion_list[key] = value

    def resolve_type(self):
        if self.types[self.field] == 'bool':
            if self.text.lower() == 'false':
                self.text = False
            elif self.text.lower() == 'true':
                self.text = True
            else:
                raise DBExceptions.UnexpectedValue("expected bool")
        if self.types[self.field] == 'int':
            try:
                self.text = int(self.text)
            except ValueError:
                raise DBExceptions.UnexpectedValue("expected int")
        if self.types[self.field] == 'float':
            try:
                self.text = float(self.text)
            except ValueError:
                raise DBExceptions.UnexpectedValue("expected float")
        if self.types[self.field] == 'ObjectId':
            try:
                self.text = ObjectId(self.text)
            except ValueError:
                raise DBExceptions.UnexpectedValue("expected ObjectId")

