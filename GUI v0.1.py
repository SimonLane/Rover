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
from skimage.transform import rescale
Polynomial = np.polynomial.Polynomial
import csv, threading, queue
import imageio.v2 as iio


class Rover(QtGui.QMainWindow):
    def __init__(self):
        super(Rover, self).__init__()
        arm_address = "/dev/cu.usbmodem4305501"
        wheel_address = "/dev/cu.usbmodem134618801"
        fps = 10

        
        # # connect to power/arm board
        self.arm = serial.Serial(port=arm_address, baudrate=115200, timeout=0.5)
        time.sleep(0.5) #essential to have this delay!
        self.arm.write(str.encode("/hello;\n"))

        reply = self.arm.readline().strip()
        print('reply:',reply)
        if reply == b'power and arm board':
            print('power board connection established')
        else:
            print('no power board connection')
            self.arm.close()
        
        
        # connect to wheels board
        self.wheel = serial.Serial(port=wheel_address, baudrate=115200, timeout=0.5)
        time.sleep(0.5) #essential to have this delay!
        self.wheel.write(str.encode("/hello;\n"))

        reply = self.wheel.readline().strip()
        print('reply:',reply)
        if reply == b'wheels board':
            print('wheel board connection established')
        else:
            print('no wheels board connection')
            self.wheel.close()
        
        # connect to cameras
        self.cam1 = iio.get_reader("<video1>")
        self.cam2 = iio.get_reader("<video2>")

        # build GUI
        self.initUI()
        
        
        # connect to spectrometer
        
 # TIMERS  
# cameras
        self.getCamFeed = QtCore.QTimer()
        self.getCamFeed.setSingleShot(False)
        self.getCamFeed.timeout.connect(lambda: self.display_cams())
        refresh_interval = int(1000/fps)
        self.getCamFeed.start(refresh_interval) 
# power/arm
        self.getPowerReport = QtCore.QTimer()
        self.getPowerReport.setSingleShot(False)
        self.getPowerReport.timeout.connect(lambda: self.update_power_arm())
        self.getPowerReport.start(5000) 
        
    def update_power_arm(self):
        self.arm.write(str.encode("/report_power;"))
        reply = self.arm.readline().strip()
        print('reply:',reply)
    
    
    def display_cams(self):   
        
        fr1 = self.cam1.get_next_data()  # mast cam
        im1 = np.rot90(fr1,3).copy() #        image flip (horizontal axis) and rotation (90 deg anti-clockwise)
        im1 = np.fliplr(im1)
        self.cam1plot.setImage(im1, autoLevels=True)

        fr2 = self.cam2.get_next_data()  # arm cam
        im2 = np.rot90(fr2,3).copy() #        image flip (horizontal axis) and rotation (90 deg anti-clockwise)
        im2 = np.fliplr(im2)
        self.cam2plot.setImage(im2, autoLevels=True)

    
    def initUI(self):
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                #Setup main Window
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
                #Setup Panes
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# BOXES
        self.TimerBox                   = QtGui.QGroupBox('Countdown Timer')
        self.Cam1Box                    = QtGui.QGroupBox('Mast Cam')
        self.Cam2Box                    = QtGui.QGroupBox('Arm Cam')
        self.SpectraBox                 = QtGui.QGroupBox('Spectrometer')
        self.ArmBox                     = QtGui.QGroupBox('Arm')
        self.WheelsBox                  = QtGui.QGroupBox('Wheels')
        self.PowerBox                   = QtGui.QGroupBox('Power')

# TIMER
        self.TimerBox.setLayout(QtGui.QGridLayout())
        self.TimerText                  = QtGui.QLabel("05:00:00")
        self.TimerText.setStyleSheet("color: #b02020")
        TimerFont = QtGui.QFont("Impact", 300, QtGui.QFont.Bold) 
        self.TimerText.setAlignment(QtCore.Qt.AlignCenter)
        self.TimerText.setFont(TimerFont)
        self.TimerBox.layout().addWidget(self.TimerText,                        0, 0, 5, 12)
        
# POWER
        self.PowerBox.setLayout(QtGui.QGridLayout())
        bat_n = [1,2]
        bat_p = [90,75]
        self.batWidget = pg.PlotWidget()
        self.bat_graph = pg.BarGraphItem(x = bat_n, height = bat_p, width = 0.6, brush ='g')
        self.batWidget.addItem(self.bat_graph)
        self.PowerBox.layout().addWidget(self.batWidget,                        0,0,10,10)
        
# CAMERAS
        self.Cam1Box.setLayout(QtGui.QGridLayout())
        self.cam1plot                    = pg.ImageView(view=pg.PlotItem())
        self.cam1plot.ui.roiBtn.hide()
        self.cam1plot.ui.menuBtn.hide()
        self.cam1plot.ui.histogram.hide()
        self.cam1plot.setLevels(0,255)
        self.Cam1Box.layout().addWidget(self.cam1plot,                          0,0,10,10)
        
        self.Cam2Box.setLayout(QtGui.QGridLayout())
        self.cam2plot                    = pg.ImageView(view=pg.PlotItem())
        self.cam2plot.ui.roiBtn.hide()
        self.cam2plot.ui.menuBtn.hide()
        self.cam2plot.ui.histogram.hide()
        self.cam2plot.setLevels(0,255)
        self.Cam2Box.layout().addWidget(self.cam2plot,                          0,0,10,10)
#==============================================================================
# Overall assembly
#==============================================================================
        self.WidgetGroup                   = QtGui.QGroupBox('')
        self.WidgetGroup.setLayout(QtGui.QGridLayout())
         
        self.WidgetGroup.layout().addWidget(self.TimerBox,                      0, 12, 5, 12)
        self.WidgetGroup.layout().addWidget(self.Cam1Box,                       0, 0,8, 8)
        self.WidgetGroup.layout().addWidget(self.Cam2Box,                       8, 0,8, 8)
        self.WidgetGroup.layout().addWidget(self.SpectraBox,                    5, 12, 5, 12)
        self.WidgetGroup.layout().addWidget(self.ArmBox,                        10,12, 6, 4)               
        self.WidgetGroup.layout().addWidget(self.WheelsBox,                     10,16, 6, 4) 
        self.WidgetGroup.layout().addWidget(self.PowerBox,                      10,20, 6, 4)    

        self.setCentralWidget(self.WidgetGroup)
        
# Signal square
        self.signal                     = QtGui.QLabel('', self)  
        self.signal.setGeometry(QtCore.QRect(screenWidth-50,0,50,50))
        self.signal.setStyleSheet("background-color: #FF0000")
        
        



    def closeEvent(self, event): #to do upon GUI being closed
        self.getCamFeed.stop()
        self.getPowerReport.stop()
        # self.checkSerial.stop()
        self.arm.close()
        self.wheel.close()
        # self.cam1.close()
        # self.cam2.close()
        

if __name__ == '__main__':
    app = 0
    app = QtGui.QApplication(sys.argv)
    gui = Rover()
    gui.show()
    app.exec_()
