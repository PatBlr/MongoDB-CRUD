import sys
import json
from datetime import datetime, date
from bson import json_util
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTreeWidgetItem, QScrollArea, QWidget, QPushButton, QGridLayout, QLayout, QFrame)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QEvent
import DBExceptions
from Create import (create_label, update_label, create_inputbox, update_inputbox, create_button, update_button,
                    create_combo, update_combo, create_textbox, update_textbox, create_tree, update_tree, create_list,
                    update_list, create_tabview, update_tabview, create_scrollarea)
from DBConnector import DBConnector
from QueryGenerator import QueryGenerator
from bson import json_util

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.width = 1400
        self.height = 810
        self.setWindowTitle('MongoDB Query Generator')
        self.options = [
            "does not equal",
            "equals",
            "greater than",
            "less than",
            "greater or equal",
            "less or equal",
            "in",
            "not in",
            "contains",
            "starts with",
            "ends with"
        ]
        self.projections = {}
        self.amount_statements = 0
        self.font = QFont()
        self.font_disabled = self.font
        self.font.setPointSize(9)
        self.obj = {}
        self.resize(self.width, self.height)
        self.connector = DBConnector()
        self.init_ui()

    def init_ui(self):
        # create GUI
        # TODO: Refactor Exceptions
        try:
            # inputbox for database string
            ib_connect = create_inputbox(widget=self, obj_name="ib_connect", font=self.font, size=[400, 30],
                                         pos=[10, 10], text="localhost:27017")
            self.obj[ib_connect.objectName()] = ib_connect
            # connection button - will attempt to connect after clicking
            button_connect = create_button(widget=self, obj_name="button_connect", font=self.font, size=[100, 30],
                                           pos=[420, 10], text="connect")
            button_connect.clicked.connect(self.on_connect)
            self.obj[button_connect.objectName()] = button_connect
            # display for connection status or errors / warnings
            label_connected = create_label(widget=self, obj_name="label_connect", font=self.font, size=[500, 30],
                                           pos=[550, 10], text="not connected", color="red")
            self.obj[label_connected.objectName()] = label_connected
            # combobox for databases
            combo_dbs = create_combo(widget=self, obj_name="combo_dbs", font=self.font, size=[200, 30],
                                     pos=[10, 50], enabled=False)
            combo_dbs.installEventFilter(self)
            combo_dbs.currentTextChanged.connect(self.on_db_changed)
            self.obj[combo_dbs.objectName()] = combo_dbs
            # tree with collection->value|type for
            tree = create_tree(widget=self, obj_name="tree", font=self.font, size=[500, 700],
                               pos=[10, 100], headers=["Name", "Type"])
            tree.itemDoubleClicked.connect(self.on_item_selected)
            self.obj[tree.objectName()] = tree

            box_select = QWidget(self)
            box_select.resize(770, 0)
            # box_select.setStyleSheet("background-color: blue")

            box_layout = QGridLayout(box_select)

            create_scrollarea(widget=self, child=box_select, size=[800, 250], pos=[550, 100])
            # scrollarea.setStyleSheet("background-color: white")

            self.add_dialog_buttons(widget=box_select, layout=box_layout)
            self.add_statement(widget=box_select, start=100 * self.amount_statements, layout=box_layout)

            # TODO
            button_find = create_button(widget=self, obj_name="button_find", font=self.font, size=[100, 30],
                                        pos=[550, 460], color="grey", text="Find", enabled=False)
            button_find.clicked.connect(self.on_find)
            self.obj[button_find.objectName()] = button_find
            # TODO
            combo_projection = create_combo(widget=self, obj_name="combo_projection", font=self.font, size=[200, 30],
                                            pos=[550, 400], enabled=False, checkable=True,
                                            stditem="Projection: (include)")
            combo_projection.view().pressed.connect(self.on_projection_clicked)
            combo_projection.installEventFilter(self)
            self.obj[combo_projection.objectName()] = combo_projection
            # TODO
            tabview = create_tabview(widget=self, obj_name="tabview", size=[800, 300], pos=[550, 500],
                                     tabs=["Query", "Result"], enabled=False)
            self.obj[tabview.objectName()] = tabview
            # display for generated query - pos is relative to the tabview - (-1) removes visible border
            tb_query = create_textbox(widget=self.obj["tab_query"], obj_name="tb_query", font=self.font,
                                      size=[400, 275], pos=[-1, -1], enabled=True)
            self.obj[tb_query.objectName()] = tb_query
            tb_query_pretty = create_textbox(widget=self.obj["tab_query"], obj_name="tb_query_pretty", font=self.font,
                                      size=[400, 275], pos=[400, -1], enabled=True)
            self.obj[tb_query_pretty.objectName()] = tb_query_pretty
            # display for results - pos is relative to the tabview - (-1) removes visible border
            tb_result = create_textbox(widget=self.obj["tab_result"], obj_name="tb_result", font=self.font,
                                       size=[800, 275], pos=[-1, -1], enabled=True)
            self.obj[tb_result.objectName()] = tb_result
        except Exception as e:
            print(e, "init_ui")

    def eventFilter(self, target, event):
        # filter Mousewheel on target - prevents scrolling on combobox
        if event.type() == QEvent.Wheel:
            return True
        if event.type() == QEvent.FocusIn:
            print(target, target.objectName())
            return True
        return False

    def on_projection_clicked(self, index):
        # pyqtSlot for combo_projection
        # on click toggle checkstate and remove from / append to projection list
        item = self.obj["combo_projection"].model().itemFromIndex(index)
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
            if type_name != "":
                # TODO - lw select und label type aendern
                update_list(widget=self, obj_name=f"lw_select{self.amount_statements}", clear=True, items=[collection, name])
                update_label(widget=self, obj_name=f"label_type{self.amount_statements}", text=type_name + ":")
                self.fill_projections(self.possible_projections(collection))
                update_combo(widget=self, obj_name="combo_projection", enabled=True, items=self.projections,
                             stditem="Projection: (include)", checkable=True)

    def on_connect(self):
        # pyqtSlot for button_connect
        # on click connect to the database with the URI entered in ib_connect
        db_uri = ""
        try:
            db_uri = self.obj["ib_connect"].text()
        except KeyError as e:
            print(e)
        try:
            self.connector.connect(db_uri)
            self.connector.check_connection()
            # enable gui widgets
            update_label(widget=self, obj_name="label_connect", text="connected", color="green")
            update_combo(widget=self, obj_name="combo_dbs", items=self.connector.get_list_dbs(), enabled=True)
            update_tree(widget=self, obj_name="tree", enabled=True)
            # TODO - von hier
            update_label(widget=self, obj_name=f"label_select1", color="black")
            update_list(widget=self, obj_name=f"lw_select1", enabled=True)
            update_combo(widget=self, obj_name=f"combo_select1", items=self.options, enabled=True, stditem="Options:")
            update_label(widget=self, obj_name=f"label_type1", color="black")
            update_inputbox(widget=self, obj_name=f"ib_select1", enabled=True)
            # TODO - bis hier die 1 umaendern ???
            update_button(widget=self, obj_name="button_add", enabled=True)
            update_combo(widget=self, obj_name="combo_projection", enabled=True, stditem="Projection: (include)")
            update_button(widget=self, obj_name="button_find", enabled=True, color="black")
            update_tabview(widget=self, obj_name="tabview", enabled=True)
        except DBExceptions.ConnectionFailure as e:
            update_textbox(widget=self, obj_name="tb_query", text=str(e), color="red")
            print(e)
        except Exception as e:
            print(e)

    def on_db_changed(self, value):
        # pyqtSlot for combo_dbs
        # on index change fill treeview beneath with all collections and it's fields
        # TODO: Refactor Exceptions
        # clear UI
        self.obj["tree"].clear()
        for i in range(1, self.amount_statements):
            self.obj[f"lw_select{i}"].clear()
            self.obj[f"combo_select{i}"].setCurrentIndex(0)
            self.obj[f"ib_select{i}"].clear()
        update_combo(widget=self, obj_name="combo_projection", stditem="Projection: (include)")
        self.obj["tb_query"].clear()
        self.obj["tb_result"].clear()
        if value == "":
            return
        try:
            self.connector.set_db(value)
            self.connector.update_types()
            types = self.connector.get_types()
            # add every collection to the tree without a type
            for collection in self.connector.get_list_collections():
                item = QTreeWidgetItem(self.obj["tree"], [collection, ''])
                entries = self.connector.get_collection_entries(collection, distinct=True)
                if entries is not None:
                    self.rec_fill_subitem(item, collection, entries, types)
        except Exception as e:
            print(e)

    def on_find(self):
        statements = {}
        statement = {}
        # clear TBs first
        update_textbox(widget=self, obj_name="tb_query", text="")
        update_textbox(widget=self, obj_name="tb_query_pretty", text="")
        update_textbox(widget=self, obj_name="tb_result", text="")
        try:
            for i in range(1, self.amount_statements+1):
                if self.obj[f"lw_select{i}"].count() < 2:
                    update_textbox(widget=self, obj_name="tb_query", text="No field selected", color="red")
                    return
                if self.obj[f"combo_select{i}"].currentText() not in self.options:
                    update_textbox(widget=self, obj_name="tb_query", text="No option selected", color="red")
                    return
                if i > 1 and self.obj[f"combo_clause{i}"].currentText() not in ["and", "or"]:
                    update_textbox(widget=self, obj_name="tb_query", text="No clause selected", color="red")
                    return
                statement = {"collection": self.obj[f"lw_select{i}"].item(0).text(),
                             "field": self.obj[f"lw_select{i}"].item(1).text(),
                             "option": self.obj[f"combo_select{i}"].currentText(),
                             "text": self.obj[f"ib_select{i}"].text(),
                             }
                statement["expected_type"] = self.connector.get_types()[statement["collection"]][statement["field"]]
                clause = self.obj[f"combo_clause{i}"].currentText() if i > 1 else ""
                statement["clause"] = clause
                statements[f"statement{i}"] = statement
            qgenerator = QueryGenerator(statements, self.connector.get_types()[statement["collection"]], self.projections)
            query = qgenerator.get_query()
            print(query)
            query = json_util.loads(query.replace("'", '"'))
            projection = qgenerator.get_projection()
            result = self.connector.find(collection=statement["collection"], query=query, projection=projection)
            update_textbox(widget=self, obj_name="tb_query", text=qgenerator.get_query_string())
            update_textbox(widget=self, obj_name="tb_query_pretty", text=qgenerator.get_query_string_pretty())
            update_textbox(widget=self, obj_name="tb_result", text="")
            if len(result) == 0:
                update_textbox(widget=self, obj_name="tb_result", text="No Result")
            else:
                update_textbox(widget=self, obj_name="tb_result", text=f"{len(result)} result(s) found:\n")
                for res in result:
                    text = json.dumps(res, indent=4, sort_keys=False, default=self.json_serial)
                    self.obj["tb_result"].append(text)
        except json.JSONDecodeError as e:
            update_textbox(widget=self, obj_name="tb_query", text=str(e)+"\nPossible mistakes:\n"
                                                                         "Bools: [true/false]\n", color="red")
        except Exception as e:
            print(e, "in on_find")

    def check_scrollbar(self):
        # can't check visibility by itself, so this is a makeshift solution
        sender = self.sender().parent().parent()
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
                                   size=[200, 30], pos=[150, widget.height()-30], enabled=False)
        button_add.clicked.connect(lambda: self.add_statement(widget=widget, start=100 * self.amount_statements, layout=layout,
                                                              enabled=True))
        self.obj[button_add.objectName()] = button_add
        button_del = create_button(widget=widget, obj_name="button_del", text="Remove last Statement", font=self.font,
                                   size=[200, 30], pos=[350, widget.height()-30])
        button_del.clicked.connect(lambda: self.remove_last_statement(widget=widget))
        self.obj[button_del.objectName()] = button_del

    def add_statement(self, widget, start, layout, enabled=False):
        if self.amount_statements > 0:
            if self.obj[f"lw_select{self.amount_statements}"].count() == 0:
                error = "Please specify Field before adding new and / or Statement"
                update_textbox(widget=self, obj_name="tb_query", text=error, color="red")
                return
            if self.obj[f"combo_select{self.amount_statements}"].currentText() not in self.options:
                error = "Please specify Option before adding new and / or Statement"
                update_textbox(widget=self, obj_name="tb_query", text=error, color="red")
                return
        if self.amount_statements > 1:
            if self.obj[f"combo_clause{self.amount_statements}"].currentText() not in ["and", "or"]:
                error = "Please specify Clause before adding new and / or Statement"
                update_textbox(widget=self, obj_name="tb_query", text=error, color="red")
                return
        self.amount_statements += 1
        try:
            color = "black" if enabled else "grey"

            if self.amount_statements > 1:
                combo_clause = create_combo(widget=widget, obj_name=f"combo_clause{self.amount_statements}", font=self.font,
                                            size=[0, 0], pos=[0, 0], stditem="Clause:", items=["and", "or"],
                                            enabled=True)
                layout.addWidget(combo_clause, self.amount_statements, 0, Qt.AlignTop)
                self.obj[combo_clause.objectName()] = combo_clause
            # label indicator for the select field
            label_select = create_label(widget=widget, obj_name=f"label_select{self.amount_statements}", font=self.font, size=[400, 30],
                                        pos=[10, start+1], text="Field:", color=color, enabled=enabled)
            layout.addWidget(label_select, self.amount_statements, 1, Qt.AlignTop)
            self.obj[label_select.objectName()] = label_select
            # list widget containing the clicked field
            lw_select = create_list(widget=widget, obj_name=f"lw_select{self.amount_statements}", font=self.font, size=[200, 30],
                                    pos=[10, start+30], horizontal=True, enabled=enabled)
            lw_select.setMaximumSize(1000, 26)
            lw_select.horizontalScrollBar().rangeChanged.connect(self.check_scrollbar)
            layout.addWidget(lw_select, self.amount_statements, 2, Qt.AlignTop)
            self.obj[lw_select.objectName()] = lw_select
            # combobox containing all possible options for comparison
            combo_select = create_combo(widget=widget, obj_name=f"combo_select{self.amount_statements}", font=self.font, size=[200, 30],
                                        pos=[250, start+30], enabled=enabled, stditem="Options:", items=self.options)
            combo_select.installEventFilter(self)
            layout.addWidget(combo_select, self.amount_statements, 3, Qt.AlignTop)
            self.obj[combo_select.objectName()] = combo_select
            # label indicator for the type of the selected field
            label_type = create_label(widget=widget, obj_name=f"label_type{self.amount_statements}", font=self.font, size=[400, 30],
                                      pos=[500, start+30], text="type:", color=color, enabled=enabled)
            layout.addWidget(label_type, self.amount_statements, 4, Qt.AlignTop)
            self.obj[label_type.objectName()] = label_type
            # inputbox for the comparison string
            ib_select = create_inputbox(widget=widget, obj_name=f"ib_select{self.amount_statements}", font=self.font, size=[200, 30],
                                        pos=[570, start+30], enabled=enabled)
            ib_select.installEventFilter(self)
            layout.addWidget(ib_select, self.amount_statements, 5, Qt.AlignTop)
            self.obj[ib_select.objectName()] = ib_select
            widget.resize(widget.width(), widget.height()+100)

            update_button(widget=self,obj_name="button_add", pos=[150, widget.height()-30])
            update_button(widget=self,obj_name="button_del", pos=[350, widget.height()-30], enabled=enabled)
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
            self.obj[widget].setParent(None)
            del self.obj[widget]

    def possible_projections(self, collection):
        projections = []
        for key in self.connector.get_collection_entries(collection, distinct=True):
            projections.append(key)
        return projections

    def fill_projections(self, projections):
        self.projections.clear()
        for projection in projections:
            self.projections[projection] = 1

    def closeEvent(self, a0: QtGui.QCloseEvent):
        self.connector.close()

    def json_serial(self, obj):
        # source: https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))

def main():
    app = QApplication(sys.argv)
    demo = MainWindow()
    demo.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
