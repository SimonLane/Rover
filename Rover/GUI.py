#!/usr/bin/env python3
# v4l2-ctl --list-devices
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 21 14:01:43 2023

@author: Simon Lane
"""
import cv2

from PyQt5 import QtGui, QtCore, Qt, QtWidgets
from PyQt5.QtGui import QFontDatabase
import sys, time, serial
import serial.tools.list_ports
import pyqtgraph as pg
import numpy as np
from skimage.transform import rescale

import threading, queue

from wasatch.WasatchBus    import WasatchBus
from wasatch.WasatchDevice import WasatchDevice

import Gamepad

class Rover(QtWidgets.QMainWindow):
    def __init__(self):
        super(Rover, self).__init__()
        self.first_cam = True
        self.spectrometer_connected = False
        self.thread_to_GUI = queue.Queue()
        self.thread_active = False
        self.spectra = []
        self.wavenumbers = []
        self.pixels=1952
        self.HOST_TO_DEVICE=0x40
        self.DEVICE_TO_HOST=0xC0
        self.BUFFER_SIZE = 8
        self.integration_time = 500 #integration time
        self.averages = 2
        self.gain = 20  # gain
        self.laser_power = 100
        self.bat_p = [0,0] #battery percentage
        self.bat_v = [16.6,16.6] #battery voltage
        self.use_uCs = True
        self.camRate = 50 #(ms between frame grabs)
        
#         varables for Rover controllers
        self.mode = 0 		# 0: startup - all off; 1: driving mode; 2: arm mode; 3: raman mode;
        self.user = 0 		# 0: participant; 1: moderator;
        self.speed = 0		# float -1.0 to +1.0; forward/backwards speed
        self.turn = 0		# float -1.0 to +1.0; turning speed
        self.arm_speed = 0  # float -1.0 to +1.0; arm forwards/backwards progression
        self.arm_turn = 0
# connect to game controllers
        
        # Wait for a connection
        if not Gamepad.available():
            print('Please connect Xbox Adaptive Controller...')
            while not Gamepad.available():
                time.sleep(1.0)
        self.X1C = Gamepad.XboxTWO(joystickNumber=0)
        print('Adaptive Controller connected :)',self.X1C.joystickNumber)
        sys.stdout.flush()
        
        if not Gamepad.available():
            print('Please connect Xbox Adaptive Controller...')
            while not Gamepad.available():
                time.sleep(1.0)
        self.X2C = Gamepad.XboxONE(joystickNumber=1)
        print('Handheld controller connected :)',self.X2C.joystickNumber)
        sys.stdout.flush()
        
        self.X1C.startBackgroundUpdates()
        self.X2C.startBackgroundUpdates()
#     define button handler functions
        self.X1C.addButtonPressedHandler(0, lambda:self.buttonPress(1,0))
        self.X1C.addButtonPressedHandler(1, lambda:self.buttonPress(1,1))
        self.X1C.addButtonPressedHandler(2, lambda:self.buttonPress(1,2))
        self.X1C.addButtonPressedHandler(3, lambda:self.buttonPress(1,3))
        self.X1C.addButtonPressedHandler(4, lambda:self.buttonPress(1,4))
        self.X1C.addButtonPressedHandler(5, lambda:self.buttonPress(1,5))
        self.X1C.addButtonPressedHandler(6, lambda:self.buttonPress(1,6))
        self.X1C.addButtonPressedHandler(7, lambda:self.buttonPress(1,7))
        self.X1C.addButtonPressedHandler(8, lambda:self.buttonPress(1,8))
        self.X1C.addButtonPressedHandler(9, lambda:self.buttonPress(1,9))
        self.X1C.addButtonPressedHandler(10, lambda:self.buttonPress(1,10))
        self.X2C.addButtonPressedHandler(0, lambda:self.buttonPress(2,0))
        self.X2C.addButtonPressedHandler(1, lambda:self.buttonPress(2,1))
        self.X2C.addButtonPressedHandler(2, lambda:self.buttonPress(2,2))
        self.X2C.addButtonPressedHandler(3, lambda:self.buttonPress(2,3))
        self.X2C.addButtonPressedHandler(4, lambda:self.buttonPress(2,4))
        self.X2C.addButtonPressedHandler(5, lambda:self.buttonPress(2,5))
        self.X2C.addButtonPressedHandler(6, lambda:self.buttonPress(2,6))
        self.X2C.addButtonPressedHandler(7, lambda:self.buttonPress(2,7))
        self.X2C.addButtonPressedHandler(8, lambda:self.buttonPress(2,8))
        self.X2C.addButtonPressedHandler(9, lambda:self.buttonPress(2,9))
        self.X2C.addButtonPressedHandler(10, lambda:self.buttonPress(2,10))
#  define axis handlers

        self.X1C.addAxisMovedHandler(4, self.axisMove_speed_C1)
        self.X1C.addAxisMovedHandler(3, self.axisMove_turn_C1)
        self.X2C.addAxisMovedHandler(4, self.axisMove_speed_C2)
        self.X2C.addAxisMovedHandler(3, self.axisMove_turn_C2)

                


# connect to CAMERAS
        print('connecting to cam')        

        cam1_port = 0
        cam2_port = 0

        for i in range(0,7):
            cam1 = cv2.VideoCapture(i)
            ret, fr1 = cam1.read()
            cam1.release()
            if ret is True:
                cam1_port = i
                break
                  
        for i in range(cam1_port+1,7):
            cam2 = cv2.VideoCapture(i)
            ret, fr2 = cam2.read()
            cam2.release()
            if ret is True:
                cam2_port = i
                break
#         
        print('camera ports:',cam1_port,cam2_port)
        self.cam1 = cv2.VideoCapture(cam1_port)
        self.cam2 = cv2.VideoCapture(cam2_port)
        self.cam1.set(3,320)
        self.cam1.set(4,240)
        self.cam2.set(3,320)
        self.cam2.set(4,240)
        
# Connect to TEENSY BOARDS
        if self.use_uCs:
            arm_address = None
            wheel_address = None
            ports = list(serial.tools.list_ports.comports())
            str_ports = []
            for p in ports:
                str_ = "%s" %p
                str_ports.append(str_.split()[0])

#             print(str_ports)
            # Set addresses
            for port in str_ports:
#                 print('testing:', port)
                p = serial.Serial(port=port, baudrate=115200, timeout=0.5)
                time.sleep(0.2) #essential to have this delay!
                p.write(str.encode("/hello;\n"))
                time.sleep(0.2)
                reply = p.readline().strip()
#                 print('reply:',reply)
                if reply == b'power and arm board':
                    print('match: power n arm')
                    arm_address = port
                if reply == b'wheels board':
                    print('match: wheels')
                    wheel_address = port
                p.close()

            if arm_address is None:
                raise RuntimeError("Failed to find ARM address")

            if wheel_address is None:
                raise RuntimeError("Failed to find WHEEL address")
            
# connect to power/arm board
            self.arm_serial = serial.Serial(port=arm_address, baudrate=115200, timeout=0.5)
            time.sleep(0.5) #essential to have this delay!
            self.arm_serial.write(str.encode("/hello;\n"))
            reply = self.arm_serial.readline().strip()
#             print('reply:',reply)
            if reply == b'power and arm board': print('power board connection established')
            else:
                print('power board connection failed')
                self.arm_serial.close()
# connect to wheels board
            self.wheel = serial.Serial(port=wheel_address, baudrate=115200, timeout=0.5)
            time.sleep(0.5) #essential to have this delay!
            self.wheel.write(str.encode("/hello;\n"))
            reply = self.wheel.readline().strip()
#             print('reply:',reply)
            if reply == b'wheels board': print('wheel board connection established')
            else:
                print('wheel board connection failed')
                self.wheel.close()

        # build GUI
        self.initUI()
# connect to spectrometer
#         try:
#             self.instalise_spectrometer()
#             self.spectrometer_connected = True
#         except Exception as e:
#             print("Did not connect with spectrometer")
#             print(e)
  
# TIMERS  
# cameras
        self.getCamFeed = QtCore.QTimer()
        self.getCamFeed.setSingleShot(False)
        self.getCamFeed.timeout.connect(lambda: self.display_cams())
        self.getCamFeed.start(self.camRate) 
# power/arm
        if self.use_uCs:
            self.getPowerReport = QtCore.QTimer()
            self.getPowerReport.setSingleShot(False)
            self.getPowerReport.timeout.connect(lambda: self.update_power_arm())
            self.getPowerReport.start(5000) 
# dummy spectra timer       
#         self.specTimer = QtCore.QTimer()
#         self.specTimer.setSingleShot(False)
#         self.specTimer.timeout.connect(lambda: self.grab_spectra())
#         self.specTimer.start(5000) 
# task management       
        self.task_checker = QtCore.QTimer()
        self.task_checker.setSingleShot(False)
        self.task_checker.timeout.connect(lambda: self.check_tasks())
        self.task_checker.start(100)
# game controller check    
        sys.stdout.flush()
        if self.use_uCs:
            self.game_checker = QtCore.QTimer()
            self.game_checker.setSingleShot(False)
            self.game_checker.timeout.connect(lambda: self.check_controllers())
            self.game_checker.start(100)

    
    def buttonPress(self,controller, button):
        print('Button', button, 'presed by controller', controller)
        if button == 3: # user change
            if self.user == 1: self.user = 2
            else: self.user = 1
            
        if controller == self.user:
            if button == 2: self.mode = 1
            if button == 0: self.mode = 2
            if button == 1: self.mode = 3
    
    def axisMove_speed_C1(self, position):  #controller 1 changing speed
        if(self.mode == 1 and self.user == 1): self.speed = int(position * 1000)
        if(self.mode == 2 and self.user == 1): self.arm_speed 	= int(position * 1000)
    
    def axisMove_speed_C2(self, position):  #controller 1 changing speed
        if(self.mode == 1 and self.user == 2): self.speed = int(position * 1000)
        if(self.mode == 2 and self.user == 2): self.arm_speed = int(position * 1000)
    
    def axisMove_turn_C1(self, position):  #controller 1 changing speed
        if(self.mode == 1 and self.user == 1): self.turn = int(position * 1000)
        if(self.mode == 2 and self.user == 1): self.arm_turn = int(position * 1000)
    
    def axisMove_turn_C2(self, position):  #controller 1 changing speed
        if(self.mode == 1 and self.user == 2): self.turn = int(position * 1000)
        if(self.mode == 2 and self.user == 2): self.arm_turn = int(position * 1000)
    
    def check_controllers(self):
        if self.mode == 1:
            self.arm_serial.write(str.encode("/speed.%s.%s;" %(self.speed,self.turn)))

        if self.mode == 2:
            print(self.arm_speed)
            print(self.arm_turn)



    def check_tasks(self):
        if self.thread_to_GUI.qsize()>0:
            print("spectra picked up from queue")
            task = self.thread_to_GUI.get()
            self.display_spectra(task[0])
            self.thread_active = False
            
    def grab_spectra(self): #launches get_spectra() in a thread
        print(" launching thread to get spectra ")
        self.spectraThread = threading.Thread(target=self.get_spectra, name="get spectra", args=())
        self.spectraThread.start()
        self.thread_active = True
        
    
    def get_spectra(self):          #  get the spectra
        print("thread started")
        # DARK
        self.dev.hardware.set_laser_enable(False)
        time.sleep(self.integration_time/1000)
        response = self.dev.acquire_spectrum()
        d_spec = response.spectrum

        # LIGHT
        self.dev.hardware.set_laser_enable(True)
        time.sleep(self.integration_time/1000)
        response = self.dev.acquire_spectrum()
        l_spec = response.spectrum
        self.dev.hardware.set_laser_enable(False)
        print("spectra acquired by thread")
        # SUBTRACT
        d_spec = np.array(d_spec)
        l_spec = np.array(l_spec)
        b_spec = self.normalise(np.subtract(l_spec,d_spec))
        self.thread_to_GUI.put([b_spec])  #returns spectra via a queue (thread safe)
        print("spectra added to queue")
        
    def display_spectra(self, b_spec):
        self.spec_plot.getPlotItem().clear()
        self.spec_plot.plot(x=self.wavenumbers,y=b_spec)
        
        
        
    def instalise_spectrometer(self):
        bus = WasatchBus()
        device_id = bus.device_ids[0]
        print("found %s" % device_id)
        
        device = WasatchDevice(device_id)
        if not device.connect():
            print("connection failed")
            sys.exit(1)
        
        print("connected to %s %s with %d wavenumbers from (%.2f, %.2f)" % (
            device.settings.eeprom.model,
            device.settings.eeprom.serial_number,
            device.settings.pixels(),
            device.settings.wavenumbers[0],
            device.settings.wavenumbers[-1]))
        
        self.dev = device
        self.fid = device.hardware
        self.dev.hardware.set_integration_time_ms(self.integration_time)
        self.dev.hardware.set_detector_gain(self.gain)
        self.dev.settings.state.scans_to_average = self.averages
        self.dev.settings.state.free_running_mode= False
        self.dev.settings.state.raman_mode_enabled = True
        self.wavenumbers = device.settings.wavenumbers    
    
    def normalise(self, _in):
        scaled = np.interp(_in,(_in.min(),_in.max()),(0,65000))
        kernel = [0.2, 0.2, 0.2, 0.2, 0.2]
        smoothed = np.convolve(scaled, kernel, mode='same')
        return smoothed
    
    def update_power_arm(self):
        self.arm_serial.write(str.encode("/report.power;"))
        reply = self.arm_serial.readline().strip()
        power_data = reply.decode("utf-8").split("\t")
        self.bat_v = [float(power_data[1]),float(power_data[3])]
        self.bat_p[0] = max(    ((self.bat_v[0]-16.6)/4.2)*100.0,0) # express as percentage
        self.bat_p[1] = max(    ((self.bat_v[1]-16.6)/4.2)*100.0,0) 
        print(self.bat_p)
        driver_colors ={'Bat 1': self.hex_colour(self.bat_p[0]), 'Bat 2': self.hex_colour(self.bat_p[1])}
        
        self.bat_graph.setOpts(height=self.bat_p, x=[0,1], brushes=[driver_colors[driver] for driver in driver_colors])
        
    def hex_colour(self, p):
        if p > 50:return QtGui.QColor(0,255,0)
        if p > 20:return QtGui.QColor(255,255,0)
        return QtGui.QColor(255,0,0)
        
    
    def display_cams(self):   
        if(self.first_cam):
            self.cam2.grab()
            ret, fr1 = self.cam1.retrieve() 			# mast cam
            fr1 = cv2.resize(fr1, (640,480),interpolation = cv2.INTER_CUBIC)
            im1 = QtGui.QImage(fr1.data, 620, 480, 1920, QtGui.QImage.Format_BGR888)
            self.cam1Label.setPixmap(QtGui.QPixmap.fromImage(im1))
            self.cam1Label.setFixedSize(640,480)
            self.first_cam = False
        else:
            self.cam1.grab()
            ret, fr2 = self.cam2.retrieve()   			# arm cam
            fr2 = cv2.resize(fr2, (640,480),interpolation = cv2.INTER_CUBIC)
            fr2 = cv2.rotate(fr2, cv2.ROTATE_180)
            im2 = QtGui.QImage(fr2 .data, 620, 480, 1920, QtGui.QImage.Format_BGR888)
            self.cam2Label.setPixmap(QtGui.QPixmap.fromImage(im2))
            self.first_cam = True

    
    def initUI(self):
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                #Setup main Window
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.setWindowTitle('Rover Control Panel')
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtGui.QColor(00,00,00))
        self.setPalette(palette)
        
        sizePolicyMin = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicyMin.setHorizontalStretch(0)
        sizePolicyMin.setVerticalStretch(0)
        screen       =  QtWidgets.QApplication.desktop().screenGeometry().getCoords()
        screenHeight = screen[-1]
        screenWidth  = screen[-2]
        self.setGeometry(0, 0, screenWidth*1, screenHeight*1)
          
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                #Setup Panes
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# BOXES
        self.TimerBox                   = QtWidgets.QGroupBox('Countdown Timer')
        self.Cam1Box                    = QtWidgets.QGroupBox('Mast Cam')
        self.Cam2Box                    = QtWidgets.QGroupBox('Arm Cam')
        self.SpectraBox                 = QtWidgets.QGroupBox('Spectrometer')
        self.ArmBox                     = QtWidgets.QGroupBox('Arm')
        self.WheelsBox                  = QtWidgets.QGroupBox('Wheels')
        self.PowerBox                   = QtWidgets.QGroupBox('Power')

# TIMER
        self.TimerBox.setLayout(QtWidgets.QGridLayout())
        self.TimerText                  = QtWidgets.QLabel("05:00:00")
        self.TimerText.setStyleSheet("color: #b02020")
        TimerFont = QtGui.QFont("FreeMono", 100, QtGui.QFont.Bold) 
        self.TimerText.setAlignment(QtCore.Qt.AlignCenter)
        self.TimerText.setFont(TimerFont)
        self.TimerBox.layout().addWidget(self.TimerText,                        0, 0, 5, 12)
        
# POWER
        self.PowerBox.setLayout(QtWidgets.QGridLayout())
#         self.bat_lab = ['Battery 1', 'Battery 2']
        xval = [1,2]

        self.batWidget = pg.PlotWidget()
        self.bat_graph = pg.BarGraphItem(x = xval, height = self.bat_p, width = 0.8, brush ='r')
        
#         ticks = list(enumerate(self.bat_lab))
#         ax = self.batWidget.getAxis('bottom')
#         ax.setTicks([ticks])
        
        self.batWidget.setYRange(0,100)
        self.batWidget.setXRange(0,1)
        self.batWidget.addItem(self.bat_graph)
        self.PowerBox.layout().addWidget(self.batWidget,                        0,0,10,10)
        
        self.b1_v = QtWidgets.QLabel('16.6V')
        self.b2_v = QtWidgets.QLabel('16.6V')
        
# CAMERAS
        self.Cam1Box.setLayout(QtWidgets.QGridLayout())
        self.cam1Label = QtWidgets.QLabel()
        self.Cam1Box.layout().addWidget(self.cam1Label,                          0,0,10,10)
        
        self.Cam2Box.setLayout(QtWidgets.QGridLayout())
        self.cam2Label = QtWidgets.QLabel()
        self.Cam2Box.layout().addWidget(self.cam2Label,                          0,0,10,10)
        
        
 # SPECTROMETER
        self.SpectraBox.setLayout(QtWidgets.QGridLayout())
        self.spec_plot                    = pg.PlotWidget()
        self.spec_plot.setYRange(0,65000)
#         self.SpectraBox.layout().addWidget(self.spec_plot,                      0,8,3,8)
#==============================================================================
# Overall assembly
#==============================================================================
        self.WidgetGroup                   = QtWidgets.QGroupBox('')
        self.WidgetGroup.setLayout(QtWidgets.QGridLayout())
        
        self.WidgetGroup.layout().addWidget(self.Cam1Box,                       0, 0,  8, 10)
        self.WidgetGroup.layout().addWidget(self.Cam2Box,                       8, 0,  8, 10) 
        
        self.WidgetGroup.layout().addWidget(self.TimerBox,                      0, 10, 5, 10)
        self.WidgetGroup.layout().addWidget(self.SpectraBox,                    5, 10, 5, 10)
        
        self.WidgetGroup.layout().addWidget(self.ArmBox,                        10,10, 6, 4)               
        self.WidgetGroup.layout().addWidget(self.WheelsBox,                     10,14, 6, 4) 
        self.WidgetGroup.layout().addWidget(self.PowerBox,                      10,18, 6, 2)    

        self.setCentralWidget(self.WidgetGroup)
        
# Signal square
        self.signal                     = QtWidgets.QLabel('', self)  
        self.signal.setGeometry(QtCore.QRect(screenWidth-50,0,50,50))
        self.signal.setStyleSheet("background-color: #FF0000")
        

    def closeEvent(self, event): #to do upon GUI being closed
#         self.specTimer.stop()
        self.task_checker.stop()
        if self.use_uCs:
            self.getPowerReport.stop()
            self.arm_serial.close()
            self.wheel.close()
        
        self.getCamFeed.stop()
        self.cam1.release()
        self.cam2.release()
#         self.dev.disconnect()
        self.game_checker.stop()
        self.X2C.disconnect()
        self.X1C.disconnect()

if __name__ == '__main__':
    app = 0
    app = QtWidgets.QApplication(sys.argv)
    gui = Rover()
    gui.show()
    app.exec_()

