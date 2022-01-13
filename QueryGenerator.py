# author: pbleeker

class QueryGenerator:
    query = {"projection": [], "collection": [], "condition": []}

    def __init__(self, coll, selection, cond):
        self.query["collection"] = coll
        self.query["projection"] = selection
        self.query["condition"] = cond
        # self.generate()

    def generate(self):
        pass
        # # if no argument given or "*" as all, selection is "all" -> empty string
        # if self.query["projection"] == [] or self.query["projection"] == "*":
        #     projection = ""
        # else:
        #     projection = '{'
        #     for x in self.query["projection"]:
        #         projection += f'"{x}": 1'
        #         if x != self.query["projection"][-1]:
        #             projection += ','
        #     projection += '}'
        # cond = '{'
        # cond += self.query["condition"]
        # cond += '}'
        #
        # return self.query["collection"], projection, cond

