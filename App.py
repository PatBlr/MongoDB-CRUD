import sys
from PyQt5.QtWidgets import (QApplication, QWidget)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QEvent
import DBExceptions
# from WinCreate import WinCreate
from WinRead import WinRead
from WinUpdate import WinUpdate
from WinDelete import WinDelete
from Create import (create_label, update_label, create_inputbox, create_button,
                    create_combo, update_combo,
                    create_tabview, update_tabview)
from DBConnector import DBConnector


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.width = 1400
        self.height = 810
        self.resize(self.width, self.height)
        self.setWindowTitle('MongoDB Query Generator')
        self.options = [
            "equals",
            "does not equal",
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
        self.objects = {}
        self.font = QFont()
        self.font.setPointSize(9)
        self.connector = DBConnector()
        self.win_read = None
        self.win_update = None
        self.win_delete = None
        self.init_ui()

    def init_ui(self):
        # inputbox for database string
        ib_connect = create_inputbox(widget=self, obj_name="ib_connect", font=self.font, size=[400, 30],
                                     pos=[10, 10], text="localhost:27017")
        self.objects[ib_connect.objectName()] = ib_connect
        # connection button - will attempt to connect after clicking
        button_connect = create_button(widget=self, obj_name="button_connect", font=self.font, size=[100, 30],
                                       pos=[420, 10], text="connect")
        button_connect.clicked.connect(self.__on_connect)
        self.objects[button_connect.objectName()] = button_connect
        # display for connection status or errors / warnings
        label_connected = create_label(widget=self, obj_name="label_connect", font=self.font, size=[500, 30],
                                       pos=[550, 10], text="not connected", color="red")
        self.objects[label_connected.objectName()] = label_connected
        # combobox for databases
        combo_dbs = create_combo(widget=self, obj_name="combo_dbs", font=self.font, size=[200, 30],
                                 pos=[10, 50], enabled=False, stditem="Database:")
        combo_dbs.installEventFilter(self)
        combo_dbs.currentTextChanged.connect(self.__on_db_changed)
        self.objects[combo_dbs.objectName()] = combo_dbs
        tabview = create_tabview(widget=self, obj_name="tabview", size=[self.width, self.height], pos=[0, 100],
                                 tabs=["Create", "Read", "Update", "Delete"], enabled=False, obj_list=self.objects)
        self.objects[tabview.objectName()] = tabview

        # self.win_create = WinCreate(self.objects["tab_read"], self.connector, self.options)
        self.win_read = WinRead(self.objects["tab_read"], self)
        self.win_update = WinUpdate(self.objects["tab_update"], self)
        self.win_delete = WinDelete(self.objects["tab_delete"], self)

    def eventFilter(self, target, event):
        # filter Mousewheel on target - prevents scrolling on combobox
        if event.type() == QEvent.Wheel:
            return True
        return False

    def __on_connect(self):
        # pyqtSlot for button_connect
        # on click connect to the database with the URI entered in ib_connect
        db_uri = ""
        try:
            db_uri = self.objects["ib_connect"].text()
        except KeyError as e:
            print(e)
        try:
            self.connector.connect(db_uri)
            self.connector.check_connection()
            # enable gui widgets
            update_label(widget=self, obj_name="label_connect", text="connected", color="green")
            update_combo(widget=self, obj_name="combo_dbs", items=self.connector.get_list_dbs(), enabled=True,
                         stditem="Database:")
        except DBExceptions.ConnectionFailure as e:
            print(e)
        except Exception as e:
            print(e)

    def __on_db_changed(self, value):
        # pyqtSlot for combo_dbs
        # on index change fill treeview beneath with all collections and it's fields
        # TODO: Refactor Exceptions
        if value == "Database:" or value == "":
            return
        try:
            update_tabview(widget=self, obj_name="tabview", enabled=True)
            self.connector.set_db(value)
            self.connector.update_types()
            self.update_children()
        except Exception as e:
            print(e)

    def update_children(self):
        # TODO: Update child widgets
        # if self.win_create is not None:
        #     self.win_create.update_ui()
        if self.win_read is not None:
            self.win_read.update_ui()
        if self.win_update is not None:
            self.win_update.update_ui()
        if self.win_delete is not None:
            self.win_delete.update_ui()

def main():
    app = QApplication(sys.argv)
    demo = App()
    demo.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
