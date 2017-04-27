def get_text(obj):
    """
    This function takes a GUI child widget that contains text and returns the text as string.
    :param obj: Any text yielding widget
    :return: Widget's text (str)
    """
    if str(type(obj)) == "<class 'PyQt5.QtWidgets.QLineEdit'>":
        if obj.text() == '':
            return obj.placeholderText()
        else:
            return obj.text()
    elif str(type(obj)) == "<class 'PyQt5.QtWidgets.QTextEdit'>":
        return obj.toPlainText()
    elif str(type(obj)) == "<class 'PyQt5.QtWidgets.QListWidget'>":
        return obj.currentItem().text()
    elif str(type(obj)) == "<class 'PyQt5.QtWidgets.QComboBox'>":
        return obj.currentText()
    elif str(type(obj)) == "<class 'PyQt5.QtWidgets.QTableWidgetItem'>":
        return obj.text()