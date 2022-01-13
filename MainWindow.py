import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem
from PyQt5.QtGui import QFont
import DBExceptions
from Create import (create_label, update_label, create_inputbox, create_button, create_combo, update_combo,
    create_textbox, update_textbox, create_tree, update_tree)
from DBConnector import DBConnector


def main():
    app = QApplication(sys.argv)
    demo = MainWindow()
    demo.show()
    sys.exit(app.exec_())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.width = 1400
        self.height = 810
        self.setWindowTitle('MongoDB Query Generator')
        self.font = QFont()
        self.obj = {}
        self.font.setPointSize(9)
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
            # self.obj.append(button_connect)
            self.obj[button_connect.objectName()] = button_connect
            # display for connection status or errors / warnings
            label_connected = create_label(widget=self, obj_name="label_connect", font=self.font, size=[500, 30],
                                           pos=[550, 10], text="not connected", color="red")
            # self.obj.append(label_connected)
            self.obj[label_connected.objectName()] = label_connected
            # display for results
            tb_result = create_textbox(widget=self, obj_name="tb_result", font=self.font, size=[800, 300],
                                       pos=[550, 500], enabled=True)
            # self.obj.append(tb_result)
            self.obj[tb_result.objectName()] = tb_result
            # combobox for databases
            combo_dbs = create_combo(widget=self, obj_name="combo_dbs", font=self.font, size=[200, 30],
                                     pos=[10, 50], enabled=False)
            combo_dbs.currentTextChanged.connect(self.on_combo_changed)
            # self.obj.append(combo_dbs)
            self.obj[combo_dbs.objectName()] = combo_dbs
            # tree with collection->value|type for
            tree = create_tree(widget=self, obj_name="tree", font=self.font, size=[500, 700],
                               pos=[10, 100], headers=["Name", "Type"])
            # self.obj.append(tree)
            self.obj[tree.objectName()] = tree
            print(self.obj)
        except Exception as e:
            print(e, "init_ui")

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
            update_combo(widget=self, obj_name="combo_dbs", items=self.connector.get_list_dbs(), index=-1, enabled=True)
            update_textbox(widget=self, obj_name="tb_result", enabled=True)
            update_tree(widget=self, obj_name="tree", enabled=True)

        except DBExceptions.ConnectionFailure as e:
            update_textbox(widget=self, obj_name="tb_result", text=str(e), color="red")
            print(e)

    def on_combo_changed(self, value):
        # pyqtSlot for combo_dbs
        # on index change fill treeview beneath with all collections and it's fields
        # TODO: Refactor Exceptions
        self.obj["tree"].clear()
        if value == "":
            return
        try:
            self.connector.set_db(value)
            self.connector.update_types()
            # add every collection to the tree without a type
            for collection in self.connector.get_list_collections():
                item = QTreeWidgetItem(self.obj["tree"], [collection, ''])
                entries = self.connector.get_collection_entries(collection, distinct=True)
                # add every key and it's corresponding type collection in tree
                if entries is not None:
                    for key in entries:
                        QTreeWidgetItem(item, [key, self.connector.get_types()[collection][key]])
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
