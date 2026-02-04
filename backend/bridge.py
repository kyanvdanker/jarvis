from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

class Backend(QObject):
    messageAdded = pyqtSignal(str, str)
    projectsUpdated = pyqtSignal(list)
    filesUpdated = pyqtSignal(list)
    listeningChanged = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

    def add_message(self, sender, text):
        self.messageAdded.emit(sender, text)

    def set_projects(self, projects):
        self.projectsUpdated.emit(projects)

    def set_files(self, files):
        self.filesUpdated.emit(files)

    def set_listening(self, state: bool):
        self.listeningChanged.emit(state)
