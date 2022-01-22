import json
from pymongo import errors
from datetime import datetime, date
from bson import json_util
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QTreeWidgetItem, QWidget, QGridLayout, QMessageBox)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QEvent
import DBExceptions
from Create import (create_label, update_label, create_inputbox, create_button, update_button, create_combo,
                    create_textbox, update_textbox, create_tree, create_list, update_list, create_tabview,
                    create_scrollarea)
from QueryGenerator import QueryGenerator


class WinUpdate(QWidget):
    def __init__(self, tab, parent):
        super().__init__()
        self.tab = tab
        self.parent = parent
        self.width = 1400
        self.height = 810
        self.resize(self.width, self.height)
        self.setWindowTitle('MongoDB Query Generator')
        self.options = self.parent.options
        self.projections = {}
        self.amount_statements = 0
        self.amount_updates = 0
        self.objects = {}
        self.font = QFont()
        self.font.setPointSize(9)
        self.connector = self.parent.connector
        self.init_ui()

    def init_ui(self):
        # create GUI
        # tree with collection->value|type for
        tree = create_tree(widget=self.tab, obj_name="tree", font=self.font, size=[500, 670],
                           pos=[10, 10], headers=["Name", "Type"], enabled=True)
        tree.itemDoubleClicked.connect(self.on_item_selected)
        self.objects[tree.objectName()] = tree

        tabview_statements = create_tabview(widget=self.tab, obj_name="tabview_statements", size=[800, 250],
                                            pos=[550, 10], tabs=["Statements", "Update"], obj_list=self.objects,
                                            enabled=True)
        self.objects[tabview_statements.objectName()] = tabview_statements

        box_statements = QWidget(self.objects["tab_statements"])
        box_statements.resize(770, 0)
        box_statements.setObjectName("box_statements")
        self.objects[box_statements.objectName()] = box_statements
        box_layout = QGridLayout(box_statements)

        create_scrollarea(widget=self.objects["tab_statements"], child=box_statements, size=[800, 222], pos=[0, 0])

        self.add_dialog_buttons(widget=box_statements, layout=box_layout)
        self.add_statement(widget=box_statements, start=100 * self.amount_statements, layout=box_layout)

        box_updates = QWidget(self.objects["tab_update"])
        box_updates.resize(770, 0)
        box_updates.setObjectName("box_updates")
        self.objects[box_updates.objectName()] = box_updates
        box_layout_update = QGridLayout(box_updates)

        create_scrollarea(widget=self.objects["tab_update"], child=box_updates, size=[800, 222],
                          pos=[0, 0])

        self.add_update_buttons(widget=box_updates, layout=box_layout_update)
        self.add_update(widget=box_updates, start=100 * self.amount_updates, layout=box_layout_update)

        # TODO
        combo_update_option = create_combo(widget=self.tab, obj_name="combo_update_option", font=self.font,
                                           size=[200, 30], pos=[550, 280], enabled=True, stditem="Update:",
                                           items=["Update one", "Update all"])
        combo_update_option.installEventFilter(self)
        self.objects[combo_update_option.objectName()] = combo_update_option

        # TODO
        button_update = create_button(widget=self.tab, obj_name="button_update", font=self.font, size=[100, 30],
                                      pos=[550, 340], text="Update", enabled=True)
        button_update.clicked.connect(self.on_update)
        self.objects[button_update.objectName()] = button_update

        # TODO
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
        self.objects["tree"].clear()
        while self.amount_statements > 1:
            self.remove_last_statement(self.objects["box_statements"])
        while self.amount_updates > 1:
            self.remove_last_update(self.objects["box_updates"])
        self.objects[f"lw_select1"].clear()
        self.objects[f"combo_select1"].setCurrentIndex(0)
        self.objects[f"ib_select1"].clear()
        update_label(widget=self, obj_name="label_type1", text="")
        update_label(widget=self, obj_name="label_type_update1", text="")
        self.objects["tb_query"].clear()
        self.objects[f"lw_update1"].clear()
        self.objects[f"ib_update1"].clear()
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

    def on_item_selected(self, item):
        # pyqtSlot for tree
        # send collection and clicked field to lw of selected tab
        # figure out tab first:
        if self.objects["tabview_statements"].currentWidget().objectName() == "tab_statements":
            amount = self.amount_statements
            lw = self.objects[f"lw_select{amount}"]
            label = self.objects[f"label_type{amount}"]
        else:
            amount = self.amount_updates
            lw = self.objects[f"lw_update{amount}"]
            label = self.objects[f"label_type_update{amount}"]
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
            if amount > 1:
                compare_lw = self.objects["lw_select1"]
                if compare_lw.item(0).text() != collection:
                    update_textbox(widget=self, obj_name="tb_query",
                                   text="Please select an item of the same collection", color="red")
                    return
            if type_name != "":
                update_list(widget=self, obj_name=lw.objectName(), clear=True,
                            items=[collection, name])
                update_label(widget=self, obj_name=label.objectName(), text=type_name + ":")

    def on_update(self):
        statements = {}
        updates = []
        collection = self.objects[f"lw_select1"].item(0).text()
        # clear TBs first
        update_textbox(widget=self, obj_name="tb_query", text="")
        update_textbox(widget=self, obj_name="tb_query_pretty", text="")
        update_textbox(widget=self, obj_name="tb_result", text="")
        try:
            # check for unfilled fields
            if self.objects[f"combo_update_option"].currentText() not in ["Update one", "Update all"]:
                update_textbox(widget=self, obj_name="tb_query", text="No update option selected", color="red")
                return
            for i in range(1, self.amount_statements + 1):
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
            # create update statements
            for i in range(1, self.amount_updates + 1):
                if self.objects[f"lw_update{i}"].count() < 2:
                    update_textbox(widget=self, obj_name="tb_query", text="No field selected", color="red")
                    return
                field = self.objects[f"lw_update{i}"].item(1).text()
                argument = self.objects[f"ib_update{i}"].text()
                # if the argument is not serializable by json, enclose it in quotes
                try:
                    json.loads(argument)
                except json.JSONDecodeError:
                    argument = f'"{argument}"'
                update = f'"{field}": {argument}'
                updates.append(update)
            q_gen = QueryGenerator(statements)
            query = q_gen.get_query()
            query_string = q_gen.get_query_string()
            query_string_pretty = q_gen.get_query_string_pretty()

            # for each update in the list, append the update to the string
            string_updates = '{"$set": {'
            for i, elem in enumerate(updates):
                string_updates += str(elem)
                string_updates += ", " if i < len(updates) - 1 else ""
            string_updates += "}}"
            string_updates_pretty = q_gen.prettify(string_updates)
            dict_updates = json.loads(string_updates)

            distinct = True if self.objects["combo_update_option"].currentText() == "Update one" else False
            if distinct:
                update = self.connector.update_one
                result = self.connector.find_one(collection=collection, query=query)
                text = f"db.{collection}.updateOne({query_string}, {string_updates})"
                text_pretty = f"db.{collection}.updateOne({query_string_pretty}, {string_updates_pretty})"
                found = 1 if len(result) > 0 else 0
            else:
                update = self.connector.update
                result = self.connector.find(collection=collection, query=query)
                text = f"db.{collection}.update({query_string}, {string_updates})"
                text_pretty = f"db.{collection}.update({query_string_pretty}, {string_updates_pretty})"
                found = len(result)
            if found == 0:
                update_textbox(widget=self, obj_name="tb_result", text="Nothing to update")
            else:
                # if records were found, ask for confirmation. After that -> update or cancel
                reply = QMessageBox.question(self, "Please Confirm", f"Update {found} record(s) found?",
                                             QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
                if reply == QMessageBox.Yes:
                    updated = update(collection=collection, query=query, updates=dict_updates)
                    self.parent.update_children()
                    update_textbox(widget=self, obj_name="tb_result", text=f"{updated} record(s) updated\n")
                else:
                    update_textbox(widget=self, obj_name="tb_result", text=f"Canceled\n")
            update_textbox(widget=self, obj_name="tb_query", text=text)
            update_textbox(widget=self, obj_name="tb_query_pretty", text=text_pretty)
        except json.JSONDecodeError as e:
            update_textbox(widget=self, obj_name="tb_query", text=str(e), color="red")
        except errors.WriteError as e:
            update_textbox(widget=self, obj_name="tb_query", text=str(e), color="red")

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
                QTreeWidgetItem(item, [key, types[collection][i + key]])

    def add_dialog_buttons(self, widget, layout):
        button_add = create_button(widget=widget, obj_name="button_add", text="Add Statement", font=self.font,
                                   size=[200, 30], pos=[150, widget.height() - 30], enabled=True)
        button_add.clicked.connect(lambda: self.add_statement(widget=widget, start=100 * self.amount_statements,
                                                              layout=layout))
        self.objects[button_add.objectName()] = button_add
        button_del = create_button(widget=widget, obj_name="button_del", text="Remove last Statement", font=self.font,
                                   size=[200, 30], pos=[350, widget.height() - 30])
        button_del.clicked.connect(lambda: self.remove_last_statement(widget=widget))
        self.objects[button_del.objectName()] = button_del
    
    def add_update_buttons(self, widget, layout):
        button_add = create_button(widget=widget, obj_name="button_add_update", text="Add Update", font=self.font,
                                   size=[200, 30], pos=[150, widget.height() - 30], enabled=True)
        button_add.clicked.connect(lambda: self.add_update(widget=widget, start=100 * self.amount_updates,
                                                           layout=layout))
        self.objects[button_add.objectName()] = button_add
        button_del = create_button(widget=widget, obj_name="button_del_update", text="Remove last Update", 
                                   font=self.font, size=[200, 30], pos=[350, widget.height() - 30])
        button_del.clicked.connect(lambda: self.remove_last_update(widget=widget))
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
                                        size=[400, 30], pos=[10, start + 1], text="Field:", color="black")
            layout.addWidget(label_select, self.amount_statements, 1, Qt.AlignTop)
            self.objects[label_select.objectName()] = label_select
            # list widget containing the clicked field
            lw_select = create_list(widget=widget, obj_name=f"lw_select{self.amount_statements}", font=self.font,
                                    size=[200, 30], pos=[10, start + 30], horizontal=True, enabled=True)
            lw_select.setMaximumSize(1000, 26)
            lw_select.horizontalScrollBar().rangeChanged.connect(self.check_scrollbar)
            layout.addWidget(lw_select, self.amount_statements, 2, Qt.AlignTop)
            self.objects[lw_select.objectName()] = lw_select
            # combobox containing all possible options for comparison
            combo_select = create_combo(widget=widget, obj_name=f"combo_select{self.amount_statements}", font=self.font,
                                        size=[200, 30], pos=[250, start + 30], enabled=True, stditem="Options:",
                                        items=self.options)
            combo_select.installEventFilter(self)
            layout.addWidget(combo_select, self.amount_statements, 3, Qt.AlignTop)
            self.objects[combo_select.objectName()] = combo_select
            # label indicator for the type of the selected field
            label_type = create_label(widget=widget, obj_name=f"label_type{self.amount_statements}", font=self.font,
                                      size=[400, 30], pos=[500, start + 30], text="type:", color="black")
            layout.addWidget(label_type, self.amount_statements, 4, Qt.AlignTop)
            self.objects[label_type.objectName()] = label_type
            # inputbox for the comparison string
            ib_select = create_inputbox(widget=widget, obj_name=f"ib_select{self.amount_statements}", font=self.font,
                                        size=[200, 30], pos=[570, start + 30], enabled=True)
            ib_select.installEventFilter(self)
            layout.addWidget(ib_select, self.amount_statements, 5, Qt.AlignTop)
            self.objects[ib_select.objectName()] = ib_select
            widget.resize(widget.width(), widget.height() + 100)
            enabled = True if self.amount_statements > 1 else False
            update_button(widget=self, obj_name="button_add", pos=[150, widget.height() - 30])
            update_button(widget=self, obj_name="button_del", pos=[350, widget.height() - 30], enabled=enabled)
        except Exception as e:
            update_textbox(widget=self, obj_name="tb_query", text=e, color="red")
            self.amount_statements -= 1
            
    def add_update(self, widget, start, layout):
        if self.amount_updates > 0:
            if self.objects[f"lw_update{self.amount_updates}"].count() == 0:
                error = "Please specify Field before adding new field to update"
                update_textbox(widget=self, obj_name="tb_query", text=error, color="red")
                return
        self.amount_updates += 1
        try:
            # label indicator for the update field
            label_update = create_label(widget=widget, obj_name=f"label_update{self.amount_updates}", font=self.font,
                                        size=[400, 30], pos=[10, start + 1], text="Field:", color="black")
            layout.addWidget(label_update, self.amount_updates, 1, Qt.AlignTop)
            self.objects[label_update.objectName()] = label_update
            # list widget containing the clicked field
            lw_update = create_list(widget=widget, obj_name=f"lw_update{self.amount_updates}", font=self.font,
                                    size=[200, 30], pos=[10, start + 30], horizontal=True, enabled=True)
            lw_update.setMaximumSize(1000, 26)
            lw_update.horizontalScrollBar().rangeChanged.connect(self.check_scrollbar)
            layout.addWidget(lw_update, self.amount_updates, 2, Qt.AlignTop)
            self.objects[lw_update.objectName()] = lw_update

            # label indicator for the type of the selected field
            label_type_update = create_label(widget=widget, obj_name=f"label_type_update{self.amount_updates}",
                                             font=self.font, size=[400, 30], pos=[500, start + 30], text="",
                                             color="black")
            layout.addWidget(label_type_update, self.amount_updates, 4, Qt.AlignTop)
            self.objects[label_type_update.objectName()] = label_type_update
            # inputbox for the comparison string
            ib_update = create_inputbox(widget=widget, obj_name=f"ib_update{self.amount_updates}", font=self.font,
                                        size=[200, 30], pos=[570, start + 30], enabled=True)
            ib_update.installEventFilter(self)
            layout.addWidget(ib_update, self.amount_updates, 5, Qt.AlignTop)
            self.objects[ib_update.objectName()] = ib_update
            widget.resize(widget.width(), widget.height() + 100)
            enabled = True if self.amount_updates > 1 else False
            update_button(widget=self, obj_name="button_add_update", pos=[150, widget.height() - 30])
            update_button(widget=self, obj_name="button_del_update", pos=[350, widget.height() - 30], enabled=enabled)
        except Exception as e:
            update_textbox(widget=self, obj_name="tb_query", text=e, color="red")
            self.amount_updates -= 1

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
            widget.resize(widget.width(), widget.height() - 100)
            update_button(widget=self, obj_name="button_add", pos=[150, widget.height() - 30])
            enabled = True if self.amount_statements > 1 else False
            update_button(widget=self, obj_name="button_del", pos=[350, widget.height() - 30], enabled=enabled)
    
    def remove_last_update(self, widget):
        if not self.amount_updates == 1:
            to_delete = [f"ib_update{self.amount_updates}",
                         f"label_update{self.amount_updates}",
                         f"lw_update{self.amount_updates}",
                         f"label_type_update{self.amount_updates}"]
            self.remove_widgets(to_delete)
            self.amount_updates -= 1
            widget.resize(widget.width(), widget.height() - 100)
            update_button(widget=self, obj_name="button_add_update", pos=[150, widget.height() - 30])
            enabled = True if self.amount_updates > 1 else False
            update_button(widget=self, obj_name="button_del_update", pos=[350, widget.height() - 30], enabled=enabled)

    def remove_widgets(self, widgets):
        for widget in widgets:
            self.objects[widget].setParent(None)
            del self.objects[widget]
