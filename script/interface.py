from stl import mesh
from mpl_toolkits import mplot3d
from matplotlib import pyplot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import math
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QComboBox, QWidget, QApplication, QPushButton, QGridLayout, QLabel, QCheckBox, QInputDialog, QLineEdit, QFileDialog
import sys
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import matplotlib.animation as animation
import random
import rospy
import rosnode
from infrastructure_msgs.msg import DoorSensors
from sensor_msgs.msg import JointState
from sensor import Sensors
from items import *
import os
import atexit
import signal
import subprocess
import multiprocessing
import threading
import pandas as pd
import rosbag
import roslaunch
import uuid
import rviz
from time import sleep

#buffers for graphs
buffer = []
sensor = []
time = []

# All subwindows generated by the application
otherWindows =[]

# current process id generated by fork
pid = 0

# kill other threads when on exit
def clean():
    children = multiprocessing.active_children()
    for child_thread in children:
        child_thread.terminate()
#    global pid
#    os.kill(pid, signal.SIGKILL)


atexit.register(clean)




class Menu(QWidget):
    def __init__(self, ap = 1, arm = 1, mode = 1, parent = None, top_obj = None):
        self.parent = parent
        self.mode = mode
        self.top_obj = top_obj
        super(QWidget, self).__init__()
        self.ap = ap
        self.arm = arm
        self.comboBox = QComboBox(self)
        self.comboBox.addItem("Mode: Live")
        self.comboBox.addItem("Mode: Recorded")

        if mode == 1:
            self.comboBox.setCurrentText("Mode: Live")
        else:
            self.comboBox.setCurrentText("Mode: Recorded")

        self.comboBox.currentIndexChanged.connect(lambda: self.change())

        filler = QLabel('', self)
        filler.resize(200, 70)
        self.setFixedHeight(650)
        self.setFixedWidth(250)
        layout = QtWidgets.QVBoxLayout(self)
        sublayout = QtWidgets.QVBoxLayout(self)
        self.createApLabel()
        self.createArmLabel()
        layout.addWidget(self.comboBox)
        layout.addWidget(self.ALabel)
        layout.addWidget(self.Arm)

        layout.addStretch()

        self.buttonArray = []
        self.statusArray = []
        for i in range (12):
            self.buttonArray.append(QPushButton("FSR " + str(i+1)))
            self.statusArray.append(0)
        self.buttonArray.append(QPushButton("Distance Sensor"))
        self.statusArray.append(0)
        for i in range (13):
            layout.addWidget(self.buttonArray[i])
            layout.addStretch()
        layout.addWidget(filler)

        #Temporary workaround for lack of topic remapping options
        self.topicBox = QLineEdit(self)
        self.topicBox.textChanged.connect(self.topicChange)
        self.topicBox.setText("sensor_data")
        self.topicLabel = QLabel(self)
        self.topicLabel.setText("Sensor topic:")
        layout.addWidget(self.topicLabel)
        layout.addWidget(self.topicBox)

        self.refreshButton = QPushButton("Refresh Displayed Topic")
        self.refreshButton.clicked.connect(self.parent.refreshTopic)
        layout.addWidget(self.refreshButton)

    def topicChange(self, topic):
        self.parent.setTopic(topic)

    def change(self):
        content = self.comboBox.currentText()
        if content == 'Mode: Live':
            self.top_obj.changeMode(True)
        else:
#            clean()
            self.top_obj.changeMode(False)


    def createApLabel(self):
        self.ALabel = QComboBox(self)
        self.ALabel.addItem("Apparatus: Drawer")
        self.ALabel.addItem("Apparatus: Door")
        self.ALabel.addItem("Apparatus: Test Bed")
        if self.ap == 1:
            self.ALabel.setCurrentText("Apparatus: Drawer")
        elif self.ap == 2:
            self.ALabel.setCurrentText("Apparatus: Door")
        else:
            self.ALabel.setCurrentText("Apparatus: Test Bed")
        self.ALabel.currentIndexChanged.connect(self.changeApparatus)


    def changeApparatus(self, index):
        self.top_obj.changeApparatus(index)

    def changeArm(self, index):
        self.top_obj.changeArm(index)


    def createArmLabel(self):
        self.Arm = QComboBox(self)
        self.Arm.addItem("Arm: Kinova Jaco2")
        self.Arm.addItem("Arm: Thor Arm")
        if self.arm == 1:
            self.Arm.setCurrentText("Arm: Kinova Jaco2")
        else:
            self.Arm.setCurrentText("Arm: Thor Arm")
        self.Arm.currentIndexChanged.connect(self.changeArm)



class Add(QWidget):
    def __init__(self, p, index, num, top_obj):
        super(QWidget, self).__init__()
        self.parent = p
        self.index = index
        self.top_obj = top_obj
        if num == 1:
            self.height = 700
            self.width = 1000
        elif num == 2:
            self.height = 550
            self.width = 600
        else:
            self.width = 500
            self.height = 350
        self.setFixedWidth(self.width)
        self.setFixedHeight(self.height)
        self.c1 = QPushButton("Distance Graph")
        self.c2 = QPushButton("FSR Graph")
        self.c3 = QPushButton("3D Model")
        self.c4 = QPushButton("RViz Visualization")
        self.c6 = QPushButton("Select Test Item")
        self.c5 = QPushButton("Back")
        self.c5.setFixedWidth(80)
        self.c5.setFixedHeight(25)
        self.c5.setStyleSheet("background-color: red;")
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout1 = QtWidgets.QVBoxLayout()
        self.layout2 = QtWidgets.QHBoxLayout(self)
        self.setLayout(self.layout)
        self.layout.addStretch()
        self.layout.addLayout(self.layout1)
        self.button = QPushButton("", self)
        self.button.setStyleSheet("border-image: url(" + self.top_obj.top_vars["package_dir"] + "/src/plus.png);")
        self.button.setFixedWidth(64)
        self.button.setFixedHeight(64)
        self.button.clicked.connect(lambda:self.switchToS())
        self.c1.clicked.connect(lambda:self.parent.addDistanceGraph(self.index))
        self.c2.clicked.connect(lambda:self.parent.addFSRGraph(self.index))
        self.c3.clicked.connect(lambda:self.parent.addModel(self.index))
        self.c4.clicked.connect(lambda:self.parent.addRviz(self.index))
        self.c5.clicked.connect(lambda:self.parent.goBack(self.index))
        self.c6.clicked.connect(lambda:self.parent.addItems(self.index))
        self.layout1.addWidget(self.button)
        self.layout.addStretch()


    def switchToS(self):
        self.button.deleteLater()
        self.layout1.addStretch()
        self.layout1.addWidget(self.c1)
        self.layout1.addWidget(self.c2)
        self.layout1.addWidget(self.c3)
        self.layout1.addWidget(self.c4)
        if self.parent.apparatus == 3:
            self.layout1.addWidget(self.c6)
        self.layout1.addLayout(self.layout2)

        self.layout2.addWidget(self.c5)
        self.layout1.addStretch()


# all possible objects on the testbed
class ObjectChoice(QtWidgets.QWidget):
    def __init__(self, p):
        super(QWidget, self).__init__()
        self.parent = p
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout1 =  QtWidgets.QHBoxLayout(self)
        self.layout2 =  QtWidgets.QHBoxLayout(self)
        self.setLayout(self.layout)
        self.layout.addLayout(self.layout1)
        self.layout.addLayout(self.layout2)
        self.initItems()
        self.layout1.addWidget(self.currentItems[0])
        self.layout1.addWidget(self.currentItems[1])
        self.layout2.addWidget(self.currentItems[2])
        self.layout2.addWidget(self.currentItems[3])


    def initItems(self):
        b1 = QPushButton("objectSelection")
        b1.setFixedWidth(150)
        b1.setFixedHeight(150)
        b1.setText("Object 1")
        b1.setStyleSheet("background-color: white;")
        b2 = QPushButton("objectSelection")
        b2.setFixedWidth(150)
        b2.setFixedHeight(150)
        b2.setText("Object 1")
        b2.setStyleSheet("background-color: white;")
        b3 = QPushButton("objectSelection")
        b3.setFixedWidth(150)
        b3.setFixedHeight(150)
        b3.setText("Object 3")
        b3.setStyleSheet("background-color: white;")
        b4 = QPushButton("objectSelection")
        b4.setFixedWidth(150)
        b4.setFixedHeight(150)
        b4.setText("Object 4")
        b4.setStyleSheet("background-color: white;")
        self.currentItems = []
        self.currentItems.append(b1)
        self.currentItems.append(b2)
        self.currentItems.append(b3)
        self.currentItems.append(b4)


        b1.clicked.connect(lambda:self.changeSelection(b1))
        b2.clicked.connect(lambda:self.changeSelection(b2))
        b3.clicked.connect(lambda:self.changeSelection(b3))
        b4.clicked.connect(lambda:self.changeSelection(b4))



    def changeSelection(self, button):
        for i in self.currentItems:
            i.setStyleSheet("background-color: white;")
        button.setStyleSheet("background-color: lightgreen;")


class Window(QWidget):
    def __init__(self, ap, arm, mode, num = 4, parent = None, top_obj = None):
        super(QWidget, self).__init__()
        self.top_obj = top_obj
        self.started = 0
        #self.showMaximized()
        self.bag  = None
        self.bagData = []
        self.bagFilePath = ""
        self.parent = parent
        self.maxValue = 100
        self.currentValue = 0
        self.num = num
        self.otherWindows = []
        self.widgetArray = [0,0,0,0]
        self.currentItems = []
        self.layoutArray =  [0,0,0,0]
        self.apparatus = ap
        self.arm = arm
        self.sensor_topic = ""
        self.subscriberThread = None

        if mode == 1:
            self.top_obj.top_vars["live"] = True
        else:
            self.top_obj.top_vars["live"] = False

        self.mode = mode
        self.setWindowTitle('3dMesh')
        self.Main = QtWidgets.QVBoxLayout(self)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout2 = QtWidgets.QHBoxLayout(self)
        self.layout3 = QtWidgets.QHBoxLayout(self)
        if self.num == 4:
            self.vLayout1 = QtWidgets.QVBoxLayout(self)
            self.vLayout2 = QtWidgets.QVBoxLayout(self)
        for i in range(num):
            self.layoutArray[i] = QtWidgets.QHBoxLayout(self)
        self.setLayout(self.Main)
        self.ap = ap
        self.arm = arm
        self.menu = Menu(ap, arm, mode, self, self.top_obj)
        for i in range(num):
            self.widgetArray[i] = Add(self, i, self.num, self.top_obj)
        self.Main.addLayout(self.layout)
        self.layout.addWidget(self.menu)
        if self.num == 4:
            self.layout.addLayout(self.vLayout1)
            self.layout.addLayout(self.vLayout2)
            self.vLayout1.addLayout(self.layoutArray[0])
            self.vLayout1.addLayout(self.layoutArray[1])
            self.vLayout2.addLayout(self.layoutArray[2])
            self.vLayout2.addLayout(self.layoutArray[3])
        elif (self.num == 2):
            self.layout.addLayout(self.layoutArray[0])
            self.layout.addLayout(self.layoutArray[1])
        else:
            self.layout.addLayout(self.layoutArray[0])
        self.Main.addLayout(self.layout2)

        for i in range(num):
            self.layoutArray[i].addWidget(self.widgetArray[i])


       # self.initLabels()
        self.menu.buttonArray[0].clicked.connect(lambda:self.triggerAnimation(0))
        self.menu.buttonArray[1].clicked.connect(lambda:self.triggerAnimation(1))
        self.menu.buttonArray[2].clicked.connect(lambda:self.triggerAnimation(2))
        self.menu.buttonArray[3].clicked.connect(lambda:self.triggerAnimation(3))
        self.menu.buttonArray[4].clicked.connect(lambda:self.triggerAnimation(4))
        self.menu.buttonArray[5].clicked.connect(lambda:self.triggerAnimation(5))
        self.menu.buttonArray[6].clicked.connect(lambda:self.triggerAnimation(6))
        self.menu.buttonArray[7].clicked.connect(lambda:self.triggerAnimation(7))
        self.menu.buttonArray[8].clicked.connect(lambda:self.triggerAnimation(8))
        self.menu.buttonArray[9].clicked.connect(lambda:self.triggerAnimation(9))
        self.menu.buttonArray[10].clicked.connect(lambda:self.triggerAnimation(10))
        self.menu.buttonArray[11].clicked.connect(lambda:self.triggerAnimation(11))
        self.menu.buttonArray[12].clicked.connect(lambda:self.triggerAnimation(12))

        if self.menu.mode == 1:
            Start = QPushButton(self)
            Start.setText("Run")
            Start.clicked.connect(lambda:self.startReading())
            Stop = QPushButton(self)
            Stop.setText("Stop")
            Stop.clicked.connect(lambda:self.stopReading())
            Start.setFixedHeight(30)
            Start.setFixedWidth(150)
            Stop.setFixedHeight(30)
            Stop.setFixedWidth(150)
            self.layout2.addStretch()
            self.layout2.addWidget(Start)
            self.layout2.addWidget(Stop)
            self.layout2.addStretch()
        else:
            self.timer = QtCore.QTimer()
            self.timer.setInterval(100)
            self.timer.timeout.connect(self.startTimer)

            self.progress = QtWidgets.QProgressBar(self)
            self.progress.setMaximum(self.maxValue)
            self.progress.setValue(self.currentValue)
            self.layout2.addStretch()
            self.layout2.addWidget(self.progress)
            self.layout2.addStretch()
            self.Main.addLayout(self.layout3)
            self.Start = QPushButton(self)
            self.Start.setText("Play")
            self.Start.clicked.connect(lambda:self.swapButtonText())
            self.Left = QPushButton(self)
            self.Left.setText("<<")
            self.Left.clicked.connect(lambda:self.decreasebyFive())
            self.Right = QPushButton(self)
            self.Right.setText(">>")
            self.Right.clicked.connect(lambda:self.increaseByFive())
            self.playStatus = 0
            self.layout3.addStretch()
            self.layout3.addWidget(self.Left)
            self.layout3.addWidget(self.Start)
            self.layout3.addWidget(self.Right)
            self.layout3.addStretch()


    def setTopic(self, topic):
        self.sensor_topic = topic


    def increaseByFive(self):
        increase = (self.total_time/100)*5
        self.currentValue = self.currentValue + increase
        if self.currentValue > self.total_time:
            self.currentValue = self.total_time
        self.progress.setValue(self.currentValue)

    def startReading(self):
        if self.started == 0:
            self.started = 1

            if self.subscriberThread != None:
                if self.subscriberThread.is_alive():
                    self.subscriberThread.terminate()

            self.subscriberThread = multiprocessing.Process(target=self.readData)
            self.subscriberThread.start()
            #global pid
            #pid = os.fork()
            #if pid == 0:
            #    self.readData()


    def stopReading(self):
        self.started = 0
        #print(bagQueue)

        fileName = str(uuid.uuid4())
        if self.parent.exPath == None:
            export = os.path.dirname(self.top_obj.top_vars["package_dir"]) + "/rosbag_records"
#            export = script_path + "/../rosbag_records"
            #Creates export directory if it doesn't exist
            #TODO: Allow argument for export directory
            if not os.path.isdir(export):
                os.mkdir(export)
        else:
            export = self.parent.exPath
        self.bag = rosbag.Bag(str(export)+ "/" + str(fileName), 'w')
        while self.top_obj.top_vars["bagQueue"].empty() == 0:
            data = self.top_obj.top_vars["bagQueue"].get()
            self.writeToBag(data)

        self.bag.close()

        if self.subscriberThread != None:
            if self.subscriberThread.is_alive():
                self.subscriberThread.terminate()
            self.subscriberThread = None
        #clean()


    def onRead(self, data):
        self.top_obj.top_vars["queue"].put(data)
        self.top_obj.top_vars["distanceQueue"].put(data)
        self.top_obj.top_vars["bagQueue"].put(data)


    def writeToBag(self, data):
        msg = DoorSensors()
        msg.current_time = data.current_time
        msg.tof  = data.tof
        msg.fsr1 = data.fsr1
        msg.fsr2 = data.fsr2
        msg.fsr3 = data.fsr3
        msg.fsr4 = data.fsr4
        msg.fsr5 = data.fsr5
        msg.fsr6 = data.fsr6
        msg.fsr7 = data.fsr7
        msg.fsr8 = data.fsr8
        msg.fsr9 = data.fsr9
        msg.fsr10 = data.fsr10
        msg.fsr11 = data.fsr11
        msg.fsr12 = data.fsr12
        msg.fsr_contact_1
        msg.fsr_contact_2
        self.bag.write("sensor_data",  msg, msg.current_time)



    def readData(self):
        rospy.init_node('interface', anonymous=True)
        if len(self.sensor_topic) > 0 and self.sensor_topic[0] == '/':
            topic = self.sensor_topic[1:]
        else:
            topic = self.sensor_topic
        rospy.Subscriber(topic, DoorSensors, self.onRead)
        rospy.spin()




    def decreasebyFive(self):
        increase = (self.total_time/100)*5
        self.currentValue = self.currentValue - increase
        if (self.currentValue < 0):
            self.currentValue = 0
        self.progress.setValue(self.currentValue)


    def startTimer(self):
        self.currentValue = self.currentValue + 0.1
        if (self.currentValue >= self.total_time):
            self.swapButtonText()
        self.progress.setValue(self.currentValue)


    def refreshTopic(self):
        if self.menu.mode != 1 and self.bagFilePath:
            #self.bag  = rosbag.Bag(os.path.dirname(script_path) + '/rosbag_records/test.bag', 'r')
            self.bag  = rosbag.Bag(self.bagFilePath, 'r')
            self.t_start = rospy.Time(self.bag.get_start_time())
            t_end   = rospy.Time(self.bag.get_end_time())
            self.total_time = (t_end - self.t_start).to_sec()
            self.bagData = []
            if len(self.sensor_topic) > 0 and not self.sensor_topic[0] == '/':
                topic = '/' + self.sensor_topic
            else:
                topic = self.sensor_topic
            for topic, msg, t in self.bag.read_messages(topics=[topic]):
                self.bagData.append([msg, t])

        else:
            if self.subscriberThread != None:
                if self.subscriberThread.is_alive():
                    self.subscriberThread.terminate()
                self.subscriberThread = None

            if self.started == 1:
                self.subscriberThread = multiprocessing.Process(target=self.readData)
                self.subscriberThread.start()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.bagFilePath, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
        if self.bagFilePath:
            print("Found file")
            #self.bag  = rosbag.Bag(os.path.dirname(script_path) + '/rosbag_records/test.bag', 'r')
            self.bag  = rosbag.Bag(self.bagFilePath, 'r')
            self.t_start = rospy.Time(self.bag.get_start_time())
            t_end   = rospy.Time(self.bag.get_end_time())
            self.total_time = (t_end - self.t_start).to_sec()
            self.bagData = []
            if len(self.sensor_topic) > 0 and not self.sensor_topic[0] == '/':
                topic = '/' + self.sensor_topic
            else:
                topic = self.sensor_topic
            for topic, msg, t in self.bag.read_messages(topics=[topic]):
                self.bagData.append([msg, t])


            self.progress.setMaximum(self.total_time)
            self.progress.setValue(0)
            return 1
        return 0


    def swapButtonText(self):
        print("Hit swap button. Play status is " + str(self.playStatus))
        if self.playStatus == -1:
            if (self.openFileNameDialog()):
                self.Start.setText("Play")
                self.playStatus = 0;

        elif self.playStatus == 0:
            if self.bag  == None and self.parent.imPath != None:
                self.bagFilePath = self.parent.imPath
                self.bag  = rosbag.Bag(self.parent.imPath, 'r')
                self.t_start = rospy.Time(self.bag.get_start_time())
                t_end   = rospy.Time(self.bag.get_end_time())

                self.total_time = (t_end - self.t_start).to_sec()
                self.bagData = []
                self.jointMsgs = []
                self.jointTopic = ""
                if len(self.sensor_topic) > 0 and not self.sensor_topic[0] == '/':
                    sensor_topic = '/' + self.sensor_topic
                else:
                    sensor_topic = self.sensor_topic
                for topic, msg, t in self.bag.read_messages():
                    if sensor_topic == topic:
                        self.bagData.append([msg, t])
                    if "joint_state" in topic:
                        self.jointTopic = topic
                        self.jointMsgs.append([msg, t])

                self.progress.setMaximum(self.total_time)
                #print(self.total_time)
                self.progress.setValue(0)


            if self.bag != None:
                self.playStatus = 1
                self.timer.start()
                self.Start.setText("Stop")
        else:
            self.playStatus = 0
            self.timer.stop()
            self.Start.setText("Play")

    def goBack(self, index):
        self.widgetArray[index].deleteLater()
        self.widgetArray[index] = Add(self, index, self.num, self.top_obj)
        self.layoutArray[index].addWidget(self.widgetArray[index])


    def addDistanceGraph(self, index):
        self.widgetArray[index].deleteLater()
        self.widgetArray[index] = GraphDistance(self, index, self.num, self.top_obj)
        self.layoutArray[index].addWidget(self.widgetArray[index])


    def addFSRGraph(self, index):
        self.widgetArray[index].deleteLater()
        self.widgetArray[index] = GraphFSR(self, self.menu.statusArray, index, self.num, self.top_obj)
        self.layoutArray[index].addWidget(self.widgetArray[index])


    def addRviz(self, index):
        self.widgetArray[index].deleteLater()
        self.widgetArray[index] = RvizWidget(self, index, self.num, self.top_obj)
        self.layoutArray[index].addWidget(self.widgetArray[index])

    def addItems(self, index):
        self.widgetArray[index].deleteLater()
        for i in range (len(self.widgetArray)):
            if isinstance(self.widgetArray[i], Items):
                self.widgetArray[i].deleteLater()
                self.widgetArray[i] = Add(self, i, self.num, self.top_obj)
                self.layoutArray[i].addWidget(self.widgetArray[i])
        self.widgetArray[index] = Items(self, self.menu.statusArray, index, self.num)
        self.layoutArray[index].addWidget(self.widgetArray[index])

    def addModel(self, index):
        self.widgetArray[index].deleteLater()
        self.widgetArray[index] = GraphImage(self, self.menu.statusArray, index, self.num, self.top_obj)
        self.layoutArray[index].addWidget(self.widgetArray[index])


    def goBackToSelection(self, index):
        self.widgetArray[index].deleteLater()
        self.widgetArray[index] = Add(self, index, self.num, self.top_obj)
        self.layoutArray[index].addWidget(self.widgetArray[index])


    def triggerAnimation(self, index):
        if index == 12:
            if self.menu.statusArray[index] == 0:
                self.menu.buttonArray[index].setStyleSheet("background-color : lightgreen")
                self.menu.statusArray[index] = 1
            else:
                self.menu.statusArray[index] = 0
                self.menu.buttonArray[index].setStyleSheet("background-color : light gray")
            return


        if self.menu.statusArray[index] == 0:
            for i in range(len(self.widgetArray)):
                if isinstance(self.widgetArray[i], GraphImage):
                    self.widgetArray[i].showMesh(index)
            self.menu.statusArray[index] = 1

            self.menu.buttonArray[index].setStyleSheet("background-color : lightgreen")
        else:
            for i in range(len(self.widgetArray)):
                if isinstance(self.widgetArray[i], GraphImage):
                    self.widgetArray[i].hideMesh(index)
            self.menu.buttonArray[index].setStyleSheet("background-color : light gray")
            self.menu.statusArray[index] = 0
        for i in range(len(self.widgetArray)):
            if isinstance(self.widgetArray[i], GraphImage):
                self.widgetArray[i].setvisibleButtons(self.menu.statusArray)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.image.showPoly()
        elif event.key() == Qt.Key_Enter:
            self.image.clear()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window(1,1)
    main.resize(860, 640)
    main.show()
    sys.exit(app.exec_())
