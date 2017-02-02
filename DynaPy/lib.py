def get_text(obj):
    """
    This function takes a GUI child widget that contains text and returns the text as string.
    :param obj: Any text yielding widget
    :return: Widget's text (str)
    """
    if str(type(obj)) == "<class 'PyQt4.QtGui.QLineEdit'>":
        if obj.text() == '':
            return obj.placeholderText()
        else:
            return obj.text()
    elif str(type(obj)) == "<class 'PyQt4.QtGui.QTextEdit'>":
        return obj.toPlainText()
    elif str(type(obj)) == "<class 'PyQt4.QtGui.QListWidget'>":
        return obj.currentItem().text()
    elif str(type(obj)) == "<class 'PyQt4.QtGui.QComboBox'>":
        return obj.currentText()