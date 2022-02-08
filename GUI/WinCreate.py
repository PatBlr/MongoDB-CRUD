"""
    Copyright (C) 2022, Patrick Bleeker
    This program comes with ABSOLUTELY NO WARRANTY;
    See full notice at Main.py
"""

from PyQt5.QtWidgets import (
    QTreeWidgetItem,
    QWidget,
    QGridLayout
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QEvent
from Utility.Create import (
    create_label,
    create_inputbox,
    create_button,
    create_textbox,
    create_tree,
    create_tabview,
    create_scrollarea
)


class WinCreate(QWidget):
    def __init__(self, tab, parent):
        super().__init__()
        self.tab = tab
        self.parent = parent
        self.options = self.parent.options
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
        self.objects[tree.objectName()] = tree
        box_statements = QWidget(self.tab)
        box_statements.resize(770, 0)
        box_statements.setObjectName("box_statements")
        self.objects[box_statements.objectName()] = box_statements
        box_layout = QGridLayout(box_statements)
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

    def update_ui(self):
        # clear UI
        self.objects["tree"].clear()
        # fill tree
        types = self.connector.get_types()
        # add every collection to the tree without a type
        for collection in self.connector.get_list_collections():
            QTreeWidgetItem(self.objects["tree"], [collection, ''])

    def eventFilter(self, target, event):
        # filter Mousewheel on target - prevents scrolling on combobox
        if event.type() == QEvent.Wheel:
            return True
        return False

    def on_item_selected(self, item):
        # pyqtSlot for tree
        self.clear_layout()
        collection = item.text(0)
        items = self.connector.get_types()[collection].items()
        self.add_insert_statements(items)

    def on_insert(self):
        try:
            if self.amount_fields > 0:
                string = "{"
                for i in range(1, self.amount_fields):
                    print(i, self.amount_fields)
                    field = self.objects[f"label_field{i}"].text()
                    field_type = self.objects[f"label_type{i}"].text()
                    value = self.objects[f"ib_value{i}"].text()
                    if len(field.split(".")) > 1:
                        field = self.split_up(field.split("."))
                #
                #     if field_type == "str":
                #         value = f'"{value}"'
                #     string += f'"{field}": {value}'
                #     if i < self.amount_fields-1:
                #         string += ", "
                # string += "}"
                # print(string)
                # print(json.loads(string))
        except Exception as e :
            print(e)

    def split_up(self, text):
        print(text)
        return ""

    def add_insert_statements(self, items):
        try:
            widget = self.objects["box_statements"]
            layout = self.objects["box_layout"]
            self.amount_fields = 0
            for key, value in items:
                if value != "dict":
                    self.amount_fields += 1
                    label_field = create_label(widget=widget, obj_name=f"label_field{self.amount_fields}",
                                               font=self.font, size=[0, 0], pos=[0, 0], text=key)
                    layout.addWidget(label_field, self.amount_fields, 0, Qt.AlignTop)
                    self.objects[label_field.objectName()] = label_field
                    label_type = create_label(widget=widget, obj_name=f"label_type{self.amount_fields}", font=self.font,
                                              size=[0, 0], pos=[0, 0], text=value)
                    layout.addWidget(label_type, self.amount_fields, 1, Qt.AlignTop)
                    self.objects[label_type.objectName()] = label_type
                    ib_value = create_inputbox(widget=widget, obj_name=f"ib_value{self.amount_fields}", font=self.font,
                                               size=[0, 0], pos=[0, 0])
                    layout.addWidget(ib_value, self.amount_fields, 2, Qt.AlignTop)
                    self.objects[ib_value.objectName()] = ib_value
                    widget.resize(widget.width(), widget.height()+50)
        except Exception as e:
            print(e)

    def clear_layout(self):
        try:
            widget = self.objects["box_statements"]
            while self.amount_fields > 0:
                to_delete = [f"label_field{self.amount_fields}",
                             f"label_type{self.amount_fields}",
                             f"ib_value{self.amount_fields}"]
                self.remove_widgets(to_delete)
                self.amount_fields -= 1
                widget.resize(widget.width(), widget.height() - 100)
            print(self.amount_fields)
        except Exception as e:
            print(e)

    def remove_widgets(self, widgets):
        for widget in widgets:
            if widget in self.objects:
                self.objects[widget].setParent(None)
                del self.objects[widget]
