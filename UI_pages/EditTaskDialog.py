import sys
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from TabWidget import *
from DueDateWidget import *
from CustomDialog import *
from TagWidget import * 
from MemberWidget import * 

class EditTaskDialog(QDialog):
    def __init__(self,parent =None):
        super(EditTaskDialog,self).__init__(parent)
        self.setWindowTitle("Edit task")
        self.parent = parent
        self.tabWidget = TabWidget()
        self.tabWidget.setFont(QFont("Moon", 8, QFont.Bold))
        path = self.parent.parent.parent.parent.path
        self.dueDateWidget = DueDateWidget(self)
        self.dueDateWidget.saveDateBtn.clicked.connect(self.parent.getNewDate)

        self.tagWidget = TagWidget(self)
        #self.tagWidget.saveTagBtn.clicked.connect(self.parent.addTagLabel)

        self.editTaskTitleDialog = CustomDialog(
            self, 'Edit task title', 'Task name: ', 'Save')
        self.editTaskTitleDialog.setContentsMargins(10,40,10,40)
        self.editTaskTitleDialog.button.clicked.connect(self.handleEditTaskTitleBtn)


        self.memberWidget = MemberWidget(self)


        self.tabWidget.addTab(self.editTaskTitleDialog, QIcon(
            path+'\\editDialog.png'), " Edit")
        self.tabWidget.addTab(self.dueDateWidget, QIcon(
            path+'\\calendar.png'), " Due date")
        self.tabWidget.addTab(self.tagWidget, QIcon(
            path+'\\tag.png'), " Tags")
        self.tabWidget.addTab(self.memberWidget, QIcon(
            path+'\\multiple.png'), " Members")

        self.mainEditTask = QVBoxLayout()
        self.mainEditTask.addWidget(self.tabWidget)
        self.setFixedSize(400,300)
        self.setLayout(self.mainEditTask)
    
    def setColor(self):
        self.palette = QPalette()
        self.setAutoFillBackground(True)
        self.palette.setColor(QPalette.Window, QColor('#FAE76E'))
        self.setPalette(self.palette)

    def handleEditTaskTitleBtn(self):
        if not self.parent.validateNewTaskTitle():
            return
        
        newTaskTitle = self.parent.getNewTaskTitle()

        self.parent.setTaskTitle(newTaskTitle)
        self.parent.parent.parent.parent.editTaskTitle( self.parent.taskId, self.parent.getTaskTitle())
