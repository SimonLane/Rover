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
import imageio as iio


class Rover(QtGui.QMainWindow):
    def __init__(self):
        super(Rover, self).__init__()
        arm_address = "/dev/cu.usbmodem4305501"
        wheel_address = "/dev/cu.usbmodem134618801"
        fps = 60
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
        self.cam2 = iio.get_reader("<video0>")

        # build GUI
        self.initUI()

        # connect to spectrometer
        try:
            self.instalise_spectrometer()
            self.spectrometer_connected = True
        except Exception as e:
            print("Did not connect with spectrometer")
            print(e)
            
        
            
        
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
# dummy spectra timer       
        self.specTimer = QtCore.QTimer()
        self.specTimer.setSingleShot(False)
        self.specTimer.timeout.connect(lambda: self.grab_spectra())
        self.specTimer.start(5000) 
# task management       
        self.task_checker = QtCore.QTimer()
        self.task_checker.setSingleShot(False)
        self.task_checker.timeout.connect(lambda: self.check_tasks())
        self.task_checker.start(100)
    
    
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
        self.arm.write(str.encode("/report_power;"))
        reply = self.arm.readline().strip()
        print('reply:',reply)
    
    
    def display_cams(self):   
        if(self.first_cam):
            fr1 = self.cam1.get_next_data()  # mast cam
            im1 = np.rot90(fr1,3).copy() #        image flip (horizontal axis) and rotation (90 deg anti-clockwise)
            im1 = np.fliplr(im1)
            self.cam1plot.setImage(im1, autoLevels=True)
            self.first_cam = False
        else:
            fr2 = self.cam2.get_next_data()  # arm cam
            im2 = np.rot90(fr2,3).copy() #        image flip (horizontal axis) and rotation (90 deg anti-clockwise)
            im2 = np.fliplr(im2)
            self.cam2plot.setImage(im2, autoLevels=True)
            self.first_cam = True

    
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
        
        
 # SPECTROMETER
        self.SpectraBox.setLayout(QtGui.QGridLayout())
        self.spec_plot                    = pg.PlotWidget()
        self.spec_plot.setYRange(0,65000)
        self.SpectraBox.layout().addWidget(self.spec_plot,                      0,8,3,8)
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
        self.specTimer.stop()
        self.task_checker.stop()
        self.arm.close()
        self.wheel.close()
        self.cam1.close()
        self.cam2.close()
        

if __name__ == '__main__':
    app = 0
    app = QtGui.QApplication(sys.argv)
    gui = Rover()
    gui.show()
    app.exec_()
