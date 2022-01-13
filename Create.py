from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QComboBox, QTextBrowser, QTreeWidget

import DBExceptions


def create_label(widget, obj_name, font, text, size, pos, color="black"):
    label = QLabel(text, widget)
    label.setObjectName(obj_name)
    update_pos(label, pos)
    update_size(label, size)
    label.setFont(font)
    label.setStyleSheet(f"color: {color};")
    return label


def update_label(widget, obj_name, font=None, text=None, size=None, pos=None, color=None):
    check_prerequisites(widget)
    try:
        label = widget.obj[obj_name]
    except KeyError as e:
        raise DBExceptions.UnexpectedValue(f"No value {obj_name} in widget.obj")
    if font is not None:
        label.setFont(font)
    if text is not None:
        label.setText(text)
    if size is not None:
        update_size(label, size)
    if pos is not None:
        update_pos(label, pos)
    if text is not None:
        label.setText(text)
    if color is not None:
        label.setStyleSheet(f"color: {color};")


def create_inputbox(widget, obj_name, font, size, pos, text=None, color="black"):
    ib = QLineEdit(text, widget)
    ib.setObjectName(obj_name)
    update_pos(ib, pos)
    update_size(ib, size)
    ib.setFont(font)
    ib.setStyleSheet(f"color: {color}; background-color: white; border-color: black")
    return ib


def create_button(widget, obj_name, font, size, pos, text, color="black"):
    button = QPushButton(text, widget)
    button.setObjectName(obj_name)
    update_pos(button, pos)
    update_size(button, size)
    button.setFont(font)
    button.setStyleSheet(f"color: {color}; background-color: white; border-color: black")
    return button


def create_combo(widget, obj_name, font, size, pos, color="black", enabled=True, items=None, index=-1):
    combo = QComboBox(widget)
    combo.setObjectName(obj_name)
    combo.setFont(font)
    update_pos(combo, pos)
    update_size(combo, size)
    combo.setStyleSheet(f"color: {color}")
    combo.setEnabled(enabled)
    if items is not None:
        combo.addItems(items)
    combo.setCurrentIndex(index)
    return combo


def update_combo(widget, obj_name, font=None, size=None, pos=None, color=None, enabled=None, items=None, index=None):
    check_prerequisites(widget)
    try:
        combo = widget.obj[obj_name]
    except KeyError as e:
        raise DBExceptions.UnexpectedValue(f"No value {obj_name} in widget.obj")
    combo.clear()
    if font is not None:
        combo.setFont(font)
    if size is not None:
        update_size(combo, size)
    if pos is not None:
        update_pos(combo, pos)
    if color is not None:
        combo.setStyleSheet(f"color: {color}")
    if enabled is not None:
        combo.setEnabled(enabled)
    if items is not None:
        combo.addItems(items)
    if index is not None:
        combo.setCurrentIndex(index)



def create_textbox(widget, obj_name, font, size, pos, text="", color="black", enabled=False):
    tb = QTextBrowser(widget)
    tb.setObjectName(obj_name)
    tb.setFont(font)
    update_pos(tb, pos)
    update_size(tb, size)
    tb.setText(text)
    tb.setStyleSheet(f"color: {color}")
    tb.setEnabled(enabled)
    return tb


def update_textbox(widget, obj_name, font=None, size=None, pos=None, text=None, color=None, enabled=None):
    try:
        check_prerequisites(widget)
        try:
            tb = widget.obj[obj_name]
        except KeyError as e:
            raise DBExceptions.UnexpectedValue(f"No value {obj_name} in widget.obj")
        if font is not None:
            tb.setFont(font)
        if size is not None:
            update_size(tb, size)
        if pos is not None:
            update_pos(tb, pos)
        if text is not None:
            tb.setText(text)
        if color is not None:
            tb.setStyleSheet(f"color: {color}")
        if enabled is not None:
            tb.setEnabled(enabled)
    except (ValueError, AttributeError) as e:
        raise e.__type__.__name__(e)


def create_tree(widget, obj_name, font, size, pos, headers, color="black", enabled=False):
    tree = QTreeWidget(widget)
    tree.setObjectName(obj_name)
    tree.setFont(font)
    update_size(tree, size)
    update_pos(tree, pos)
    if isinstance(headers, list):
        tree.setHeaderLabels(headers)
    else:
        raise DBExceptions.UnexpectedValue(f"expected: list, value: {type(size).__name__}")
    tree.setEnabled(enabled)
    return tree


def update_tree(widget, obj_name, font=None, size=None, pos=None, headers=None, color=None, enabled=None):
    try:
        check_prerequisites(widget)
        try:
            tree = widget.obj[obj_name]
        except KeyError as e:
            raise DBExceptions.UnexpectedValue(f"No value {obj_name} in widget.obj")
        if font is not None:
            tree.setFont(font)
        if size is not None:
            update_size(tree, size)
        if pos is not None:
            update_pos(tree, pos)
        if headers is not None:
            tree.setHeaderLabels(headers)
        if color is not None:
            tree.setStyleSheet(f"color: {color}")
        if enabled is not None:
            tree.setEnabled(enabled)
    except (ValueError, AttributeError) as e:
        raise e.__type__.__name__(e)

def fill_():
    pass


def check_prerequisites(widget):
    if widget is None:
        raise DBExceptions.NoneType("Widget is None")
    try:
        len(widget.obj)
    except AttributeError as e:
        raise DBExceptions.NoneType("No object list available")


def update_pos(widget, pos):
    if isinstance(pos, list) and len(pos) == 2:
        widget.move(pos[0], pos[1])
    else:
        raise DBExceptions.UnexpectedValue(f"expected: list with 2 entries, value: {type(pos).__name__}")


def update_size(widget, size):
    if isinstance(size, list) and len(size) == 2:
        widget.resize(size[0], size[1])
    else:
        raise DBExceptions.UnexpectedValue(f"expected: list with 2 entries, value: {type(size).__name__}")