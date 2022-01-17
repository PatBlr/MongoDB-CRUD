import sys
import json
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTreeWidgetItem, QScrollArea, QWidget, QPushButton, QGridLayout, QLayout, QFrame)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QEvent
import DBExceptions
from Create import (create_label, update_label, create_inputbox, update_inputbox, create_button, update_button,
                    create_combo, update_combo, create_textbox, update_textbox, create_tree, update_tree, create_list,
                    update_list, create_tabview, update_tabview)
from DBConnector import DBConnector
from QueryGenerator import QueryGenerator


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
        self.selection_fields = 0
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
            box_select.move(550, 100)
            box_select.resize(700, 0)

            box_layout = QGridLayout(box_select)
            box_layout.setRowMinimumHeight(0,0)
            box_layout.setRowStretch(0, 0)

            scroll = QScrollArea(self)
            scroll.setWidget(box_select)
            scroll.move(550, 100)
            scroll.resize(800, 250)
            scroll.setFrameShape(QFrame.NoFrame)

            self.add_selection(widget=box_select, start=100*self.selection_fields, layout=box_layout)

            add = QPushButton(self)
            add.setText("add")
            add.move(700, 460)
            add.clicked.connect(lambda: self.add_selection(widget=box_select, start=100*self.selection_fields, layout=box_layout))


            # TODO
            button_find = create_button(widget=self, obj_name="button_find", font=self.font, size=[100, 30],
                                        pos=[550, 460], color="grey", text="Find", enabled=False)
            button_find.clicked.connect(self.on_find)
            self.obj[button_find.objectName()] = button_find
            # TODO
            combo_projection = create_combo(widget=self, obj_name="combo_projection", font=self.font, size=[200, 30],
                                            pos=[550, 400], enabled=False, checkable=True, stditem="Projection: (include)")
            combo_projection.view().pressed.connect(self.on_projection_clicked)
            combo_projection.installEventFilter(self)
            self.obj[combo_projection.objectName()] = combo_projection
            # TODO
            tabview = create_tabview(widget=self, obj_name="tabview", size=[800, 300], pos=[550, 500],
                                     tabs=["Query", "Result"], enabled=False)
            self.obj[tabview.objectName()] = tabview
            # display for generated query - pos is relative to the tabview - (-1) removes visible border
            tb_query = create_textbox(widget=self.obj["tab_query"], obj_name="tb_query", font=self.font,
                                      size=[800, 275], pos=[-1, -1], enabled=True)
            self.obj[tb_query.objectName()] = tb_query
            # display for results - pos is relative to the tabview - (-1) removes visible border
            tb_result = create_textbox(widget=self.obj["tab_result"], obj_name="tb_result", font=self.font,
                                       size=[800, 275], pos=[-1, -1], enabled=True)
            self.obj[tb_result.objectName()] = tb_result

            # lw_select.horizontalScrollBar().rangeChanged.connect(self.check_scrollbar)

        except Exception as e:
            print(e, "init_ui")

    def eventFilter(self, target, event):
        # filter Mousewheel on combo_projection and just return - prevents scrolling on combobox
        if target == self.obj["combo_projection"] or target == self.obj["combo_dbs"]:
            if event.type() == QEvent.Wheel:
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
                update_list(widget=self, obj_name=f"lw_select{0}", clear=True, items=[collection, name])
                update_label(widget=self, obj_name=f"label_type{0}", text=type_name+":")
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
            update_label(widget=self, obj_name=f"label_select0", color="black")
            update_list(widget=self, obj_name=f"lw_select0", enabled=True)
            update_combo(widget=self, obj_name=f"combo_select0", items=self.options, enabled=True, stditem="Options:")
            update_label(widget=self, obj_name=f"label_type0", color="black")
            update_inputbox(widget=self, obj_name=f"ib_select0", enabled=True)
            # TODO - bis hier die 0 umaendern
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
        for i in range(0, self.selection_fields):
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
        update_textbox(widget=self, obj_name="tb_result", text="")
        option = self.obj["combo_select"].currentText()
        if self.obj["lw_select"].count() > 0:
            if option in self.options:
                collection = self.obj["lw_select"].item(0).text()
                field = self.obj["lw_select"].item(1).text()
                field_type = self.connector.get_types()[collection][field]
                text = self.obj["ib_select"].text()
                try:
                    q = QueryGenerator(field, field_type, option, text, self.projections,
                                       self.connector.get_types()[collection])
                    query_str = f"db.{collection}.find({q.generate_string()})"
                    query = q.generate_query()
                    update_textbox(widget=self, obj_name="tb_query", text=query_str)
                    result = self.connector.find(collection, query[0], query[1])
                    print(type(result))
                    for x in result:
                        text = json.dumps(x, indent=4, sort_keys=False)
                        self.obj["tb_result"].append(text)
                except Exception as e:
                    update_textbox(widget=self, obj_name="tb_query", text=str(e), color="red")
            else:
                update_textbox(widget=self, obj_name="tb_query", text="No option selected", color="red")
        else:
            update_textbox(widget=self, obj_name="tb_query", text="No field selected", color="red")

    def check_scrollbar(self):
        sender = self.sender().parent().parent().objectName()
        print(sender)
        if self.sender().minimum() != self.sender().maximum():
            update_list(widget=self, obj_name=sender, size=[200, 60])
        else:
            update_list(widget=self, obj_name=sender, size=[200, 30])

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

    def add_selection(self, widget, start, layout):
        # label indicator for the select field
        label_select = create_label(widget=widget, obj_name=f"label_select{self.selection_fields}", font=self.font, size=[400, 30],
                                    pos=[10, start+1], text="Field:", color="grey")
        self.obj[label_select.objectName()] = label_select
        # list widget containing the clicked field
        lw_select = create_list(widget=widget, obj_name=f"lw_select{self.selection_fields}", font=self.font, size=[200, 30],
                                pos=[10, start+30], horizontal=True)
        self.obj[lw_select.objectName()] = lw_select
        # combobox containing all possible options for comparison
        combo_select = create_combo(widget=widget, obj_name=f"combo_select{self.selection_fields}", font=self.font, size=[200, 30],
                                    pos=[250, start+30], enabled=False, stditem="Options:", items=self.options)
        self.obj[combo_select.objectName()] = combo_select
        # label indicator for the type of the selected field
        label_type = create_label(widget=widget, obj_name=f"label_type{self.selection_fields}", font=self.font, size=[400, 30],
                                  pos=[500, start+30], text="type:", color="grey")
        self.obj[label_type.objectName()] = label_type
        # inputbox for the comparison string
        ib_select = create_inputbox(widget=widget, obj_name=f"ib_select{self.selection_fields}", font=self.font, size=[200, 30],
                                    pos=[570, start+30], enabled=False)
        self.obj[ib_select.objectName()] = ib_select
        widget.resize(widget.width(), widget.height()+100)

        layout.addWidget(label_select, self.selection_fields, 0)
        layout.addWidget(lw_select, self.selection_fields, 1)
        layout.addWidget(combo_select, self.selection_fields, 2)
        layout.addWidget(label_type, self.selection_fields, 3)
        layout.addWidget(ib_select, self.selection_fields, 4)

        self.selection_fields += 1


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

def main():
    app = QApplication(sys.argv)
    demo = MainWindow()
    demo.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
