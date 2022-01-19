from PyQt5.QtWidgets import (QLabel, QLineEdit, QPushButton, QComboBox, QTextBrowser, QTreeWidget, QHeaderView,
                             QListWidget, QTabWidget, QWidget, QScrollArea)
from PyQt5.QtGui import QStandardItem, QBrush, QColor
from PyQt5.QtCore import Qt

import DBExceptions


def create_label(widget, obj_name, font, text, size, pos, color="black", enabled=True):
    label = QLabel(text, widget)
    label.setObjectName(obj_name)
    update_pos(label, pos)
    update_size(label, size)
    label.setFont(font)
    label.setStyleSheet(f"color: {color};")
    label.setEnabled(enabled)
    return label


def update_label(widget, obj_name, font=None, text=None, size=None, pos=None, color=None):
    check_prerequisites(widget)
    try:
        label = widget.obj[obj_name]
    except KeyError:
        raise DBExceptions.UnexpectedValue(f"No value {obj_name} in widget.obj")
    if font is not None:
        label.setFont(font)
    if text is not None:
        label.setText(text)
    if size is not None:
        update_size(label, size)
    if pos is not None:
        update_pos(label, pos)
    if color is not None:
        label.setStyleSheet(f"color: {color};")


def create_inputbox(widget, obj_name, font, size, pos, text=None, color="black", enabled=True):
    ib = QLineEdit(text, widget)
    ib.setObjectName(obj_name)
    update_pos(ib, pos)
    update_size(ib, size)
    ib.setFont(font)
    ib.setStyleSheet(f"color: {color}; background-color: white; border-color: black")
    ib.setEnabled(enabled)
    return ib


def update_inputbox(widget, obj_name, font=None, text=None, size=None, pos=None, color=None, enabled=None):
    check_prerequisites(widget)
    try:
        ib = widget.obj[obj_name]
    except KeyError:
        raise DBExceptions.UnexpectedValue(f"No value {obj_name} in widget.obj")
    if font is not None:
        ib.setFont(font)
    if text is not None:
        ib.setText(text)
    if size is not None:
        update_size(ib, size)
    if pos is not None:
        update_pos(ib, pos)
    if color is not None:
        ib.setStyleSheet(f"color: {color};")
    if enabled is not None:
        ib.setEnabled(enabled)


def create_button(widget, obj_name, font, size, pos, text, color="black", enabled=True):
    button = QPushButton(text, widget)
    button.setObjectName(obj_name)
    update_pos(button, pos)
    update_size(button, size)
    button.setFont(font)
    button.setStyleSheet(f"color: {color};")
    button.setEnabled(enabled)
    return button


def update_button(widget, obj_name, font=None, size=None, pos=None, text=None, color=None, enabled=None):
    check_prerequisites(widget)
    button = widget.obj[obj_name]
    try:
        if font is not None:
            button.setFont(font)
        if size is not None:
            update_size(button, size)
        if pos is not None:
            update_pos(button, pos)
        if text is not None:
            button.setText(text)
        if color is not None:
            button.setStyleSheet(f"color: {color};")
        if enabled is not None:
            button.setEnabled(enabled)
    except (ValueError, AttributeError) as e:
        raise e.__type__.__name__(e)


def create_combo(widget, obj_name, font, size, pos, color="black", enabled=True, items=None, checkable=False,
                 stditem=""):
    combo = QComboBox(widget)
    combo.setObjectName(obj_name)
    combo.setFont(font)
    update_pos(combo, pos)
    update_size(combo, size)
    combo.setStyleSheet(f"color: {color}")
    combo.setEnabled(enabled)
    first_item = QStandardItem(stditem)
    first_item.setBackground(QBrush(QColor(200, 200, 200)))
    first_item.setSelectable(False)
    combo.model().setItem(0, 0, first_item)
    if items is not None:
        for i, field in enumerate(items):
            item = QStandardItem(field)
            if checkable:
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                item.setData(Qt.Checked, Qt.CheckStateRole)
            combo.model().setItem(i + 1, 0, item)
    return combo


def update_combo(widget, obj_name, font=None, size=None, pos=None, color=None, enabled=None, items=None,
                 checkable=False, stditem=""):
    check_prerequisites(widget)
    try:
        combo = widget.obj[obj_name]
    except KeyError:
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
    first_item = QStandardItem(stditem)
    first_item.setBackground(QBrush(QColor(200, 200, 200)))
    first_item.setSelectable(False)
    combo.model().setItem(0, 0, first_item)
    if items is not None:
        for i, field in enumerate(items):
            item = QStandardItem(field)
            if checkable:
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                item.setData(Qt.Checked, Qt.CheckStateRole)
            combo.model().setItem(i + 1, 0, item)


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


def update_textbox(widget, obj_name, font=None, size=None, pos=None, text=None, color="black", enabled=None):
    try:
        check_prerequisites(widget)
        try:
            tb = widget.obj[obj_name]
        except KeyError:
            raise DBExceptions.UnexpectedValue(f"No value {obj_name} in widget.obj")
        if font is not None:
            tb.setFont(font)
        if size is not None:
            update_size(tb, size)
        if pos is not None:
            update_pos(tb, pos)
        if text is not None:
            tb.setText(text)
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
    # stretch first header, default is: stretch last header
    # setStretchLastSection(False) is optional, might look cleaner
    tree.header().setStretchLastSection(False)
    tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
    tree.setHeaderLabels(headers)
    tree.setStyleSheet(f"color: {color};")
    tree.setEnabled(enabled)
    return tree


def update_tree(widget, obj_name, font=None, size=None, pos=None, headers=None, color=None, enabled=None):
    try:
        check_prerequisites(widget)
        try:
            tree = widget.obj[obj_name]
        except KeyError:
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


def create_list(widget, obj_name, font, size, pos, color="black", enabled=False, horizontal=False,
                scroll_always_on=False):
    lw = QListWidget(widget)
    lw.setObjectName(obj_name)
    lw.setFont(font)
    update_size(lw, size)
    update_pos(lw, pos)
    lw.setStyleSheet(f"color: {color};")
    lw.setEnabled(enabled)
    if horizontal:
        lw.setFlow(QListWidget.LeftToRight)
    if scroll_always_on:
        lw.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
    return lw


def update_list(widget, obj_name, font=None, size=None, pos=None, color=None, enabled=None, horizontal=None,
                scroll_always_on=None, clear=False, items=None):
    try:
        check_prerequisites(widget)
        try:
            lw = widget.obj[obj_name]
        except KeyError:
            raise DBExceptions.UnexpectedValue(f"No value {obj_name} in widget.obj")
        if clear:
            lw.clear()
        if font is not None:
            lw.setFont(font)
        if size is not None:
            update_size(lw, size)
        if pos is not None:
            update_pos(lw, pos)
        if color is not None:
            lw.setStyleSheet(f"color: {color}")
        if enabled is not None:
            lw.setEnabled(enabled)
        if horizontal is not None:
            if horizontal:
                lw.setFlow(QListWidget.LeftToRight)
            else:
                lw.setFlow(QListWidget.TopToBottom)
        if scroll_always_on is not None and horizontal:
            if scroll_always_on:
                lw.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            else:
                lw.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        if items is not None:
            lw.addItems(items)
    except (ValueError, AttributeError) as e:
        raise e.__type__.__name__(e)


def create_tabview(widget, obj_name, size, pos, tabs, obj_list,enabled=False):
    tv = QTabWidget(widget)
    tv.setObjectName(obj_name)
    update_size(tv, size)
    update_pos(tv, pos)
    tv.setEnabled(enabled)
    if not isinstance(tabs, list):
        raise DBExceptions.UnexpectedValue(f"expected: list, value: {type(pos).__name__}")
    for item in tabs:
        tab = QWidget()
        tab.setObjectName(f"tab_{item.lower()}")
        tv.addTab(tab, item)
        obj_list[tab.objectName()] = tab
    return tv


def update_tabview(widget, obj_name, size=None, pos=None, enabled=None):
    try:
        check_prerequisites(widget)
        try:
            tv = widget.obj[obj_name]
        except KeyError:
            raise DBExceptions.UnexpectedValue(f"No value {obj_name} in widget.obj")
        if size is not None:
            update_size(tv, size)
        if pos is not None:
            update_pos(tv, pos)
        if enabled is not None:
            tv.setEnabled(enabled)
    except (ValueError, AttributeError) as e:
        raise e.__type__.__name__(e)


def create_scrollarea(widget, child, size, pos):
    scrollarea = QScrollArea(widget)
    scrollarea.setWidget(child)
    update_size(scrollarea, size)
    update_pos(scrollarea, pos)
    return scrollarea


def check_prerequisites(widget):
    if widget is None:
        raise DBExceptions.NoneType("Widget is None")
    try:
        len(widget.obj)
    except AttributeError:
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
