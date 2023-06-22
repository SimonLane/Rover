#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 21 14:01:43 2023

@author: Simon Lane
"""
from wasatch.WasatchBus    import WasatchBus
from wasatch.WasatchDevice import WasatchDevice


from PyQt5 import QtGui, QtCore, Qt
import sys, time, serial, glob
import pyqtgraph as pg
import numpy as np
Polynomial = np.polynomial.Polynomial
import csv, threading, queue
import imageio as iio



class Rover(QtGui.QMainWindow):
    def __init__(self):
        super(Rover, self).__init__()
        arm_address = ""
        wheel_address = ""
        fps = 15
        # # connect to power/arm board
        # self.arm = serial.Serial(port=arm_address, baudrate=115200, timeout=0.5)
        # time.sleep(1) #essential to have this delay!
        # self.arm.write(str.encode("/hello;\n"))

        # reply = self.arm.readline().strip()
        # print('reply:',reply)
        # if reply == b'power and arm board':
        #     print('power board connection established')
        # else:
        #     print('no power board connection')
        #     self.arm.close()
        # # connect to wheels board
        # self.wheel = serial.Serial(port=wheel_address, baudrate=115200, timeout=0.5)
        # time.sleep(1) #essential to have this delay!
        # self.wheel.write(str.encode("/hello;\n"))

        # reply = self.wheel.readline().strip()
        # print('reply:',reply)
        # if reply == b'wheels board':
        #     print('wheel board connection established')
        # else:
        #     print('no wheels board connection')
        #     self.wheel.close()
        
        # build GUI
        self.initUI()
        
        # connect to cameras
        # self.cam1 = iio.get_reader("<video0>")
        # # self.cam2 = iio.get_reader("<video2>")
        # self.getCamFeed = QtCore.QTimer()
        # self.getCamFeed.setSingleShot(False)
        # self.getCamFeed.timeout.connect(lambda: self.display_cams())
        # refresh_interval = int(1000/fps)
        # self.getCamFeed.start(refresh_interval) 
        
        # connect to spectrometer
        
        
        
    
    def display_cams(self):
        frame = self.cam1.get_next_data()
        print(frame)
        image = np.rot90(frame,3) #        image flip (horizontal axis) and rotation (90 deg anti-clockwise)
        image = np.fliplr(image)
        self.cameraplot.setImage(image, autoLevels=False)
    
    
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                #Setup main Window
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def initUI(self):

        self.setWindowTitle('Rover Control Panel')
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtGui.QColor(78,78,78))
        self.setPalette(palette)
        
        sizePolicyMin = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicyMin.setHorizontalStretch(0)
        sizePolicyMin.setVerticalStretch(0)
        screen       =  QtGui.QApplication.desktop().screenGeometry().getCoords()
        screenHeight = screen[-1]
        screenWidth  = screen[-2]
        self.setGeometry(0, 0, screenWidth*1, screenHeight*1)
         
         
         
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                #Setup Panes/Tabs
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# BOXES
        self.TimerBox                   = QtGui.QGroupBox('Countdown Timer')
        self.Cam1Box                    = QtGui.QGroupBox('Mast Cam')
        self.Cam2Box                    = QtGui.QGroupBox('Arm Cam')
        self.SpectraBox                 = QtGui.QGroupBox('Spectrometer')
        self.ArmBox                     = QtGui.QGroupBox('Arm')
        self.WheelsBox                  = QtGui.QGroupBox('Wheels')
        self.PowerBox                   = QtGui.QGroupBox('Power')


        
        
        
        # TimerFont = QtGui.QFont("Times", 90, QtGui.QFont.Bold) 
        # i.setFont(newfont)
        # i.setStyleSheet("border: 3px solid white;")
  
        # graphs
        self.plot_1                    = pg.PlotWidget()
        self.plot_1.setYRange(0,65000)

        
        # camera
        self.cameraplot                    = pg.ImageView(view=pg.PlotItem())
        print(self.cameraplot)
        self.cameraplot.ui.roiBtn.hide()
        self.cameraplot.ui.menuBtn.hide()
        self.cameraplot.setLevels(0,125)
#==============================================================================
# Overall assembly
#==============================================================================
        self.WidgetGroup                   = QtGui.QGroupBox('')
        self.WidgetGroup.setLayout(QtGui.QGridLayout())
         
        self.WidgetGroup.layout().addWidget(self.TimerBox,                      0, 0, 5, 12)
        self.WidgetGroup.layout().addWidget(self.Cam1Box,                       0, 12,8, 8)
        self.WidgetGroup.layout().addWidget(self.Cam2Box,                       8, 12,8, 8)
        self.WidgetGroup.layout().addWidget(self.SpectraBox,                    5, 0, 5, 12)
        self.WidgetGroup.layout().addWidget(self.ArmBox,                        10,0, 6, 4)               
        self.WidgetGroup.layout().addWidget(self.WheelsBox,                     10,4, 6, 4) 
        self.WidgetGroup.layout().addWidget(self.PowerBox,                      10,8, 6, 4)    
        self.setCentralWidget(self.WidgetGroup)
        

# Signal square
        self.signal                     = QtGui.QLabel()  
        self.signal.setGeometry(QtCore.QRect(100,100,50,50))
        self.signal.setText("hello")
        self.signal.setStyleSheet("background-color: yellow")
        self.signal.move(200,300)
        self.show()


    def closeEvent(self, event): #to do upon GUI being closed
        # self.checkSerial.stop()
        # self.arm.close()
        # self.wheel.close()
        # self.cam1.close()
        pass

if __name__ == '__main__':
    app = 0
    app = QtGui.QApplication(sys.argv)
    gui = Rover()
    gui.show()
    app.exec_()
