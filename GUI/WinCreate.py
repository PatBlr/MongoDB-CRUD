"""
    Copyright (C) 2022, Patrick Bleeker
    This program comes with ABSOLUTELY NO WARRANTY;
    See full notice at Main.py
"""

import json
import pymongo.errors
from PyQt5.QtWidgets import (
    QTreeWidgetItem,
    QWidget,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QMenu,
    QAction,
    QMessageBox, QTreeWidgetItemIterator
)
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt, QEvent
from Utility.QueryGenerator import QueryGenerator
from Utility.Create import (
    create_label,
    create_inputbox,
    create_button,
    update_button,
    create_textbox,
    update_textbox,
    create_tree,
    create_tabview,
    create_scrollarea,
    create_combo
)


class WinCreate(QWidget):
    def __init__(self, tab, parent):
        super().__init__()
        self.tab = tab
        self.parent = parent
        self.options = self.parent.options
        self.selected_collection = None
        self.projections = {}
        self.amount_fields = 0
        self.objects = {}
        self.font = QFont()
        self.font.setPointSize(9)
        self.connector = self.parent.connector
        self.init_ui()

    def init_ui(self):
        # create GUI
        # tree with collection->name|type of current database
        tree = create_tree(widget=self.tab, obj_name="tree", font=self.font, size=[500, 670],
                           pos=[10, 10], headers=["Collection"], enabled=True)
        tree.itemDoubleClicked.connect(self.on_item_selected)
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(self.on_item_right_clicked)
        self.objects[tree.objectName()] = tree
        box_statements = QWidget(self.tab)
        box_statements.resize(770, 0)
        box_statements.setObjectName("box_statements")
        self.objects[box_statements.objectName()] = box_statements
        box_layout = QVBoxLayout(box_statements)
        box_layout.setObjectName("box_layout")
        self.objects[box_layout.objectName()] = box_layout
        create_scrollarea(widget=self.tab, child=box_statements, size=[800, 250], pos=[550, 10])
        # button to do a insert operation with specified params
        button_insert = create_button(widget=self.tab, obj_name="button_insert", font=self.font, size=[100, 30],
                                      pos=[550, 340], text="Insert", enabled=True)
        button_insert.clicked.connect(self.on_insert)
        self.objects[button_insert.objectName()] = button_insert
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

    def eventFilter(self, target, event):
        # filter Mousewheel on target - prevents scrolling on combobox
        if event.type() == QEvent.Wheel:
            return True
        return False

    def update_ui(self):
        # clear UI
        self.objects["tree"].clear()
        # fill tree
        # add every collection to the tree
        for collection in self.connector.get_list_collections():
            QTreeWidgetItem(self.objects["tree"], [collection])
        new_collection = QTreeWidgetItem(self.objects["tree"], ["New Collection"])
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        new_collection.setFont(0, font)

    def on_item_selected(self, item):
        # pyqtSlot for tree
        widget = self.objects["box_statements"]
        layout = self.objects["box_layout"]
        widget.resize(widget.width(), 0)
        self.clear_layout()
        if item.text(0) == "New Collection":
            self.add_dialog_buttons(widget, layout)
            self.add_new_collection(widget, layout)
            return
        self.selected_collection = item.text(0)
        items = self.connector.get_types()[self.selected_collection].items()
        self.add_insert_statements(items)

    def on_item_right_clicked(self, pos):
        item = self.objects["tree"].itemAt(pos)
        if item is None:
            return
        if item.parent() is not None:
            return
        if self.collection_count() == self.collection_index(item):
            return
        menu = QMenu()
        drop_collection = QAction("Drop Collection")
        drop_collection.triggered.connect(lambda: self.on_drop_collection(item.text(0)))
        menu.addAction(drop_collection)
        menu.exec_(QCursor.pos())

    def collection_count(self):
        # max items in tree
        count = 0
        iterator = QTreeWidgetItemIterator(self.objects["tree"])
        while iterator.value():
            count += 1
            iterator += 1
        return count

    def collection_index(self, collection):
        # collection position in tree
        count = 0
        iterator = QTreeWidgetItemIterator(self.objects["tree"])
        while iterator.value():
            count += 1
            if iterator.value() is collection:
                return count
            iterator += 1
        return count

    def on_drop_collection(self, collection):
        reply = QMessageBox.warning(self, "Please Confirm", f"Drop collection {collection}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.connector.drop_collection(collection)
            self.parent.update_children()

    def on_combo_change(self):
        # pyqtSlot for all type-combo boxes
        # set placeholder text based on the selected type
        default_text = {
            "float": "e.g. 10.0",
            "str": "e.g. Text",
            "list": "e.g. 'String', Integer, ...",
            "bool": "e.g. True",
            "int": "e.g. 10",
            "timestamp": "YYYY-MM-DD",
        }
        number = 0
        for index, char in enumerate(self.sender().objectName()):
            if char.isdigit():
                number = self.sender().objectName()[index:]
                break
        if number == 0:
            return
        self.objects[f"ib_value{number}"].setPlaceholderText(default_text[self.sender().currentText()])

    def on_insert(self):
        # pyqtSlot for insert button
        # determine if new collection
        if "ib_collection" in self.objects:
            if self.objects["ib_collection"].text() in self.connector.get_types():
                error = f"Collection {self.objects['ib_collection'].text()} already exists"
                self.error_to_tb(error)
                return
            self.selected_collection = self.objects["ib_collection"].text()
        # error-handling
        if self.selected_collection is None or self.selected_collection == "":
            error = "Please select a collection"
            self.error_to_tb(error)
            return
        if self.amount_fields == 0:
            error = "Specify at least one field"
            self.error_to_tb(error)
            return
        # format string
        string = "{"
        for i in range(1, self.amount_fields+1):
            field = self.objects[f"w_field{i}"].text()
            if isinstance(self.objects[f"w_type{i}"], QComboBox):
                field_type = self.objects[f"w_type{i}"].currentText()
                if field_type == "Type:":
                    self.error_to_tb("Please specify a type")
                    return
            else:
                field_type = self.objects[f"w_type{i}"].text()
            value = self.objects[f"ib_value{i}"].text()
            try:
                # resolve types
                if field_type == "str":
                    value = f'"{value}"'
                if field_type == "list":
                    value = f"[{value}]"
                if field_type == "int":
                    value = int(value)
                if field_type == "float":
                    value = float(value)
                if field_type == "bool":
                    if value.lower == "false":
                        value = False
                    if value.lower == "true":
                        value = True
                    else:
                        self.error_to_tb(f"Unexpected value: {value}")
            except ValueError as e:
                self.error_to_tb(e)
                return
            string += f'"{field}": {value}'
            if i < self.amount_fields:
                string += ", "
        string += "}"
        try:
            # resolve the actual string
            resolved_dict = QueryGenerator.resolve_string_to_dict(string)
            resolved_string = json.dumps(resolved_dict)
        except Exception as e:
            self.error_to_tb(e)
            return
        try:
            ids = self.connector.insert_one(self.selected_collection, resolved_dict)
        except pymongo.errors.DuplicateKeyError as e:
            self.error_to_tb(e)
            return
        except Exception as e:
            print(e)
        text = f"db.{self.selected_collection}.insertOne({resolved_string})"
        text_pretty = f"db.{self.selected_collection}.insertOne({QueryGenerator.prettify(resolved_string)})"
        self.parent.update_children()
        update_textbox(widget=self, obj_name="tb_query", text=text)
        update_textbox(widget=self, obj_name="tb_query_pretty", text=text_pretty)
        update_textbox(widget=self, obj_name="tb_result", text=f"inserted following id(s):\n{ids}")

    def error_to_tb(self, error):
        update_textbox(widget=self, obj_name="tb_query", text=str(error), color="red")
        update_textbox(widget=self, obj_name="tb_query_pretty", text="")
        update_textbox(widget=self, obj_name="tb_result", text=f"")

    def add_new_collection(self, widget, layout):
        try:
            self.amount_fields = 0
            hlayout = QHBoxLayout()
            label_collection = create_label(widget=widget, obj_name="label_collection", font=self.font,
                                            text="Collection Name:")
            hlayout.addWidget(label_collection, Qt.AlignTop)
            self.objects[label_collection.objectName()] = label_collection
            ib_collection = create_inputbox(widget=widget, obj_name="ib_collection", font=self.font)
            hlayout.addWidget(ib_collection, Qt.AlignTop)
            self.objects[ib_collection.objectName()] = ib_collection
            widget.resize(widget.width(), widget.height() + 100)
            layout.addLayout(hlayout)
            self.add_new_field(widget, layout)

        except Exception as e:
            print(e)

    def add_dialog_buttons(self, widget, layout):
        try:
            hlayout = QHBoxLayout()
            button_add = create_button(widget=widget, obj_name="button_add", text="Add Field", font=self.font,
                                       enabled=True)
            button_add.clicked.connect(lambda: self.add_new_field(widget=widget, layout=layout))
            hlayout.addWidget(button_add)
            self.objects[button_add.objectName()] = button_add
            button_del = create_button(widget=widget, obj_name="button_del", text="Remove last Field", font=self.font)
            button_del.clicked.connect(lambda: self.remove_last_field(widget=widget))
            hlayout.addWidget(button_del)
            self.objects[button_del.objectName()] = button_del
            layout.addLayout(hlayout)
        except Exception as e:
            print(e)

    def add_new_field(self, widget, layout):
        self.amount_fields += 1
        types = [
            "float",
            "str",
            "list",
            "bool",
            "int",
        ]
        hlayout = QHBoxLayout()
        label_field = create_label(widget=widget, obj_name=f"label_field{self.amount_fields}", font=self.font,
                                   text="Field name:")
        hlayout.addWidget(label_field, Qt.AlignTop)
        self.objects[label_field.objectName()] = label_field
        ib_field = create_inputbox(widget=widget, obj_name=f"w_field{self.amount_fields}", font=self.font)
        hlayout.addWidget(ib_field, Qt.AlignTop)
        self.objects[ib_field.objectName()] = ib_field
        combo = create_combo(widget=widget, obj_name=f"w_type{self.amount_fields}", font=self.font, stditem="Type:",
                             items=types)
        combo.installEventFilter(self)
        combo.currentTextChanged.connect(self.on_combo_change)
        hlayout.addWidget(combo, Qt.AlignTop)
        self.objects[combo.objectName()] = combo
        ib_value = create_inputbox(widget=widget, obj_name=f"ib_value{self.amount_fields}", font=self.font, text="")
        hlayout.addWidget(ib_value, Qt.AlignTop)
        self.objects[ib_value.objectName()] = ib_value
        widget.resize(widget.width(), widget.height() + 50)
        enabled = True if self.amount_fields > 1 else False
        update_button(widget=self, obj_name="button_del", enabled=enabled)
        layout.addLayout(hlayout)

    def remove_last_field(self, widget):
        if not self.amount_fields == 1:
            to_delete = [
                f"label_field{self.amount_fields}",
                f"w_field{self.amount_fields}",
                f"w_type{self.amount_fields}",
                f"ib_value{self.amount_fields}"
            ]
            self.remove_widgets(to_delete)
            self.amount_fields -= 1
            widget.resize(widget.width(), widget.height() - 50)
            enabled = True if self.amount_fields > 1 else False
            update_button(widget=self, obj_name="button_del", enabled=enabled)

    def add_insert_statements(self, items):
        try:
            widget = self.objects["box_statements"]
            layout = self.objects["box_layout"]
            self.amount_fields = 0
            for key, value in items:
                if value != "dict":
                    hlayout = QHBoxLayout()
                    self.amount_fields += 1
                    w_field = create_label(widget=widget, obj_name=f"w_field{self.amount_fields}",
                                           font=self.font, text=key)
                    hlayout.addWidget(w_field, Qt.AlignTop)
                    self.objects[w_field.objectName()] = w_field
                    w_type = create_label(widget=widget, obj_name=f"w_type{self.amount_fields}", font=self.font,
                                          text=value)
                    hlayout.addWidget(w_type, Qt.AlignTop)
                    self.objects[w_type.objectName()] = w_type
                    ib_value = create_inputbox(widget=widget, obj_name=f"ib_value{self.amount_fields}", font=self.font)
                    hlayout.addWidget(ib_value, Qt.AlignTop)
                    self.objects[ib_value.objectName()] = ib_value
                    widget.resize(widget.width(), widget.height()+50)
                    layout.addLayout(hlayout)
        except Exception as e:
            print(e)

    def clear_layout(self):
        try:
            widget = self.objects["box_statements"]
            while self.amount_fields > 0:
                to_delete = [f"w_field{self.amount_fields}",
                             f"label_field{self.amount_fields}",
                             f"w_type{self.amount_fields}",
                             f"ib_value{self.amount_fields}",
                             "label_collection",
                             "ib_collection",
                             "button_add",
                             "button_del"
                             ]
                self.remove_widgets(to_delete)
                self.amount_fields -= 1
                widget.resize(widget.width(), widget.height() - 100)
        except Exception as e:
            print(e)

    def remove_widgets(self, widgets):
        for widget in widgets:
            if widget in self.objects:
                self.objects[widget].setParent(None)
                del self.objects[widget]
