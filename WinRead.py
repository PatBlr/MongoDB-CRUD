import json
from PyQt5.QtWidgets import (
    QTreeWidgetItem,
    QWidget,
    QGridLayout
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QEvent
from Create import (
    create_label,
    update_label,
    create_inputbox,
    create_button,
    update_button,
    create_combo,
    update_combo,
    create_textbox,
    update_textbox,
    create_tree,
    create_list,
    update_list,
    create_tabview,
    create_scrollarea
)
from QueryGenerator import QueryGenerator


class WinRead(QWidget):
    def __init__(self, tab, parent):
        super().__init__()
        self.tab = tab
        self.parent = parent
        self.options = self.parent.options
        self.projections = {}
        self.amount_statements = 0
        self.objects = {}
        self.font = QFont()
        self.font.setPointSize(9)
        self.connector = self.parent.connector
        self.init_ui()

    def init_ui(self):
        # create GUI
        # tree with collection->name|type of current database
        tree = create_tree(widget=self.tab, obj_name="tree", font=self.font, size=[500, 670],
                           pos=[10, 10], headers=["Name", "Type"], enabled=True)
        tree.itemDoubleClicked.connect(self.on_item_selected)
        self.objects[tree.objectName()] = tree
        # scrollarea to hold the statements
        box_statements = QWidget(self.tab)
        box_statements.resize(770, 0)
        box_statements.setObjectName("box_statements")
        self.objects[box_statements.objectName()] = box_statements
        box_layout = QGridLayout(box_statements)
        create_scrollarea(widget=self.tab, child=box_statements, size=[800, 250], pos=[550, 10])
        self.add_dialog_buttons(widget=box_statements, layout=box_layout)
        self.add_statement(widget=box_statements, start=100 * self.amount_statements, layout=box_layout)
        # combobox for the projections
        combo_projection = create_combo(widget=self.tab, obj_name="combo_projection", font=self.font,
                                        size=[200, 30], pos=[550, 280], enabled=True, checkable=True,
                                        stditem="Projection: (include)")
        combo_projection.view().pressed.connect(self.on_projection_clicked)
        combo_projection.installEventFilter(self)
        self.objects[combo_projection.objectName()] = combo_projection
        # button to do a find operation with specified params
        button_find = create_button(widget=self.tab, obj_name="button_find", font=self.font, size=[100, 30],
                                    pos=[550, 340], text="Find", enabled=True)
        button_find.clicked.connect(self.on_find)
        self.objects[button_find.objectName()] = button_find
        # tabview to show generated query and result for find operation
        tabview = create_tabview(widget=self.tab, obj_name="tabview", size=[800, 300], pos=[550, 380],
                                 tabs=["Query", "Result"], enabled=True, obj_list=self.objects)
        self.objects[tabview.objectName()] = tabview
        # display for generated query - pos is relative to the tabview - (-1) removes visible border
        tb_query = create_textbox(widget=self.objects["tab_query"], obj_name="tb_query", font=self.font,
                                  size=[400, 275], pos=[-1, -1], enabled=True)
        self.objects[tb_query.objectName()] = tb_query
        tb_query_pretty = create_textbox(widget=self.objects["tab_query"], obj_name="tb_query_pretty",
                                         font=self.font, size=[400, 275], pos=[400, -1], enabled=True)
        self.objects[tb_query_pretty.objectName()] = tb_query_pretty
        # display for results - pos is relative to the tabview - (-1) removes visible border
        tb_result = create_textbox(widget=self.objects["tab_result"], obj_name="tb_result", font=self.font,
                                   size=[800, 275], pos=[-1, -1], enabled=True)
        self.objects[tb_result.objectName()] = tb_result

    def update_ui(self):
        # clear UI
        print("clearing ui")
        self.objects["tree"].clear()
        while self.amount_statements > 1:
            self.remove_last_statement(self.objects["box_statements"])
        self.objects[f"lw_select1"].clear()
        self.objects[f"combo_select1"].setCurrentIndex(0)
        self.objects[f"ib_select1"].clear()
        update_combo(widget=self, obj_name="combo_projection", stditem="Projection: (include)")
        update_label(widget=self, obj_name="label_type1", text="")
        self.objects["tb_query"].clear()
        self.objects["tb_query_pretty"].clear()
        self.objects["tb_result"].clear()
        # fill tree
        types = self.connector.get_types()
        # add every collection to the tree without a type
        for collection in self.connector.get_list_collections():
            item = QTreeWidgetItem(self.objects["tree"], [collection, ''])
            entries = self.connector.get_collection_entries(collection, distinct=True)
            if entries is not None:
                self.rec_fill_subitem(item, collection, entries, types)

    def eventFilter(self, target, event):
        # filter Mousewheel on target - prevents scrolling on combobox
        if event.type() == QEvent.Wheel:
            return True
        return False

    def on_projection_clicked(self, index):
        # pyqtSlot for combo_projection
        # on click toggle checkstate and remove from / append to projection list
        item = self.objects["combo_projection"].model().itemFromIndex(index)
        if not item.text() == "Projection: (include)":
            if item.checkState() == Qt.Checked:
                self.projections[item.text()] = 0
                item.setCheckState(Qt.Unchecked)
            else:
                self.projections[item.text()] = 1
                item.setCheckState(Qt.Checked)

    def on_item_selected(self, item):
        # pyqtSlot for tree
        # send collection and clicked field to lw_select
        name = item.text(0)
        type_name = item.text(1)
        parent = item.parent()
        collection = ""
        if parent is not None:
            while parent is not None:
                if parent.parent() is not None:
                    name = parent.text(0) + "." + name
                collection = parent.text(0)
                parent = parent.parent()
            if self.amount_statements > 1:
                if self.objects[f"lw_select{self.amount_statements-1}"].item(0).text() != collection:
                    update_textbox(widget=self, obj_name="tb_query",
                                   text="Please select an item of the same collection", color="red")
                    return
            if type_name != "":

                update_list(widget=self, obj_name=f"lw_select{self.amount_statements}", clear=True,
                            items=[collection, name])
                update_label(widget=self, obj_name=f"label_type{self.amount_statements}", text=type_name)
                self.fill_projections(self.possible_projections(collection))
                update_combo(widget=self, obj_name="combo_projection", enabled=True, items=self.projections,
                             stditem="Projection: (include)", checkable=True)

    def on_find(self):
        statements = {}
        collection = self.objects[f"lw_select1"].item(0).text()
        # clear TBs first
        update_textbox(widget=self, obj_name="tb_query", text="")
        update_textbox(widget=self, obj_name="tb_query_pretty", text="")
        update_textbox(widget=self, obj_name="tb_result", text="")
        try:
            # check for unfilled fields
            for i in range(1, self.amount_statements+1):
                if self.objects[f"lw_select{i}"].count() < 2:
                    update_textbox(widget=self, obj_name="tb_query", text="No field selected", color="red")
                    return
                if self.objects[f"combo_select{i}"].currentText() not in self.options:
                    update_textbox(widget=self, obj_name="tb_query", text="No option selected", color="red")
                    return
                if i > 1 and self.objects[f"combo_clause{i}"].currentText() not in ["and", "or"]:
                    update_textbox(widget=self, obj_name="tb_query", text="No clause selected", color="red")
                    return
                # create statements for QueryGenerator class
                statement = {"field": self.objects[f"lw_select{i}"].item(1).text(),
                             "option": self.objects[f"combo_select{i}"].currentText(),
                             "text": self.objects[f"ib_select{i}"].text()}
                clause = self.objects[f"combo_clause{i}"].currentText() if i > 1 else ""
                statement["clause"] = clause
                statements[f"statement{i}"] = statement
            # create query and output strings
            q_gen = QueryGenerator(statements)
            query = q_gen.get_query()
            query_string = q_gen.get_query_string()
            query_string_pretty = q_gen.get_query_string_pretty()
            projection = self.__filter_projection(self.projections)
            projection_pretty = q_gen.prettify(projection)
            text = f"db.{collection}.find({query_string}, {projection})"
            text_pretty = f"db.{collection}.find({query_string_pretty}, {projection_pretty})"
            # do a search operation with prepared query and projection
            result = self.connector.find(collection=collection, query=query, projection=projection)
            update_textbox(widget=self, obj_name="tb_query", text=text)
            update_textbox(widget=self, obj_name="tb_query_pretty", text=text_pretty)
            if len(result) == 0:
                update_textbox(widget=self, obj_name="tb_result", text="No records found")
            else:
                update_textbox(widget=self, obj_name="tb_result", text=f"{len(result)} record(s) found:\n")
                for res in result:
                    text = q_gen.prettify(res)
                    self.objects["tb_result"].append(text)
        except json.JSONDecodeError as e:
            update_textbox(widget=self, obj_name="tb_query", text=str(e), color="red")
        except Exception as e:
            print(e, "in on_find")

    def check_scrollbar(self):
        # can't check visibility by itself, so this is a makeshift solution
        sender = self.sender().parent().parent()
        # PyCharm says 'parent' is not callable ... don't listen to PyCharm
        if self.sender().minimum() != self.sender().maximum():
            sender.setMaximumSize(1000, 50)
        else:
            sender.setMaximumSize(1000, 26)

    def rec_fill_subitem(self, item, collection, entries, types, i=""):
        for key in entries:
            if isinstance(entries[key], dict):
                tmp = i
                i = i + key + "."
                subitem = QTreeWidgetItem(item, [key, ''])
                self.rec_fill_subitem(subitem, collection, entries[key], types, i)
                i = tmp
            else:
                QTreeWidgetItem(item, [key, types[collection][i+key]])

    def add_dialog_buttons(self, widget, layout):
        button_add = create_button(widget=widget, obj_name="button_add", text="Add Statement", font=self.font,
                                   size=[200, 30], pos=[150, widget.height()-30], enabled=True)
        button_add.clicked.connect(lambda: self.add_statement(widget=widget, start=100 * self.amount_statements,
                                                              layout=layout))
        self.objects[button_add.objectName()] = button_add
        button_del = create_button(widget=widget, obj_name="button_del", text="Remove last Statement", font=self.font,
                                   size=[200, 30], pos=[350, widget.height()-30])
        button_del.clicked.connect(lambda: self.remove_last_statement(widget=widget))
        self.objects[button_del.objectName()] = button_del

    def add_statement(self, widget, start, layout):
        if self.amount_statements > 0:
            if self.objects[f"lw_select{self.amount_statements}"].count() == 0:
                error = "Please specify Field before adding new and / or Statement"
                update_textbox(widget=self, obj_name="tb_query", text=error, color="red")
                return
            if self.objects[f"combo_select{self.amount_statements}"].currentText() not in self.options:
                error = "Please specify Option before adding new and / or Statement"
                update_textbox(widget=self, obj_name="tb_query", text=error, color="red")
                return
        if self.amount_statements > 1:
            if self.objects[f"combo_clause{self.amount_statements}"].currentText() not in ["and", "or"]:
                error = "Please specify Clause before adding new and / or Statement"
                update_textbox(widget=self, obj_name="tb_query", text=error, color="red")
                return
        self.amount_statements += 1
        try:
            if self.amount_statements > 1:
                combo_clause = create_combo(widget=widget, obj_name=f"combo_clause{self.amount_statements}",
                                            font=self.font, size=[0, 0], pos=[0, 0], stditem="Clause:",
                                            items=["and", "or"], enabled=True)
                layout.addWidget(combo_clause, self.amount_statements, 0, Qt.AlignTop)
                self.objects[combo_clause.objectName()] = combo_clause
            # label indicator for the select field
            label_select = create_label(widget=widget, obj_name=f"label_select{self.amount_statements}", font=self.font,
                                        size=[400, 30], pos=[10, start+1], text="Field:", color="black")
            layout.addWidget(label_select, self.amount_statements, 1, Qt.AlignTop)
            self.objects[label_select.objectName()] = label_select
            # list widget containing the clicked field
            lw_select = create_list(widget=widget, obj_name=f"lw_select{self.amount_statements}", font=self.font,
                                    size=[200, 30], pos=[10, start+30], horizontal=True, enabled=True)
            lw_select.setMaximumSize(1000, 26)
            lw_select.horizontalScrollBar().rangeChanged.connect(self.check_scrollbar)
            layout.addWidget(lw_select, self.amount_statements, 2, Qt.AlignTop)
            self.objects[lw_select.objectName()] = lw_select
            # combobox containing all possible options for comparison
            combo_select = create_combo(widget=widget, obj_name=f"combo_select{self.amount_statements}", font=self.font,
                                        size=[200, 30], pos=[250, start+30], enabled=True, stditem="Options:",
                                        items=self.options)
            combo_select.installEventFilter(self)
            layout.addWidget(combo_select, self.amount_statements, 3, Qt.AlignTop)
            self.objects[combo_select.objectName()] = combo_select
            # label indicator for the type of the selected field
            label_type = create_label(widget=widget, obj_name=f"label_type{self.amount_statements}", font=self.font,
                                      size=[400, 30], pos=[500, start+30], text="", color="black")
            layout.addWidget(label_type, self.amount_statements, 4, Qt.AlignTop)
            self.objects[label_type.objectName()] = label_type
            # inputbox for the comparison string
            ib_select = create_inputbox(widget=widget, obj_name=f"ib_select{self.amount_statements}", font=self.font,
                                        size=[200, 30], pos=[570, start+30], enabled=True)
            ib_select.installEventFilter(self)
            layout.addWidget(ib_select, self.amount_statements, 5, Qt.AlignTop)
            self.objects[ib_select.objectName()] = ib_select
            widget.resize(widget.width(), widget.height()+100)
            enabled = True if self.amount_statements > 1 else False
            update_button(widget=self, obj_name="button_add", pos=[150, widget.height()-30])
            update_button(widget=self, obj_name="button_del", pos=[350, widget.height()-30], enabled=enabled)
        except Exception as e:
            update_textbox(widget=self, obj_name="tb_query", text=e, color="red")
            self.amount_statements -= 1

    def remove_last_statement(self, widget):
        if not self.amount_statements == 1:
            to_delete = [f"ib_select{self.amount_statements}",
                         f"label_select{self.amount_statements}",
                         f"combo_select{self.amount_statements}",
                         f"lw_select{self.amount_statements}",
                         f"label_type{self.amount_statements}",
                         f"combo_clause{self.amount_statements}"]
            self.remove_widgets(to_delete)
            self.amount_statements -= 1
            widget.resize(widget.width(), widget.height()-100)
            update_button(widget=self, obj_name="button_add", pos=[150, widget.height() - 30])
            enabled = True if self.amount_statements > 1 else False
            update_button(widget=self, obj_name="button_del", pos=[350, widget.height() - 30], enabled=enabled)

    def remove_widgets(self, widgets):
        for widget in widgets:
            self.objects[widget].setParent(None)
            del self.objects[widget]

    def possible_projections(self, collection):
        projections = []
        for key in self.connector.get_collection_entries(collection, distinct=True):
            projections.append(key)
        return projections

    def fill_projections(self, projections):
        self.projections.clear()
        for projection in projections:
            self.projections[projection] = 1

    def __filter_projection(self, projections):
        # cannot do inclusion in exclusion projection and vice versa
        # filter out included projections (key = 1) and append it to the dict
        # _id may be in or excluded, so include it every time, despite it's value
        filtered = {}
        for key, value in projections.items():
            if value == 1 or key == '_id':
                filtered[key.replace("'", '"')] = value
        return filtered
