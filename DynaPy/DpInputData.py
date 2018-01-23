class InputData(object):
    def __init__(self):
        """
        Collection of all data input in the GUI.
        stories: dict - dictionary of objects including data from each story input in the structure tab.
        tlcd: object - data input in the tlcd tab.
        excitation: object - data input in the excitation tab.
        configurations: object - data input in the configurations tab.
        :return: None
        """
        self.stories = {}
        self.tlcd = None
        self.excitation = None
        self.configurations = None