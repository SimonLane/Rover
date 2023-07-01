# -*- coding: utf-8 -*-
"""
Outreach Spectrometer GUI


@author: Simon Lane
"""

#imports
from wasatch.WasatchBus    import WasatchBus
from wasatch.WasatchDevice import WasatchDevice

from PyQt5 import QtGui, QtCore, QtWidgets
import sys, time, serial
import pyqtgraph as pg
import numpy as np
import csv
import threading
import queue
import cv2
Polynomial = np.polynomial.Polynomial

from usb.backend import libusb1 # << WHY?

#import logging
#root = logging.getLogger()
#root.setLevel(logging.DEBUG)
#
#handler = logging.StreamHandler(sys.stdout)
#handler.setLevel(logging.DEBUG)
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#handler.setFormatter(formatter)
#root.addHandler(handler)

stage_address = "/dev/ttyACM0"

class WPSpec(QtWidgets.QMainWindow):
    def __init__(self):
        super(WPSpec, self).__init__()
        
        #test data
        self.spectra = []
        self.wavenumber = []
        self.pixels=1952
        self.HOST_TO_DEVICE=0x40
        self.DEVICE_TO_HOST=0xC0
        self.BUFFER_SIZE = 8
        self.integration_time = 1000 #integration time
        self.averages = 2
        self.gain = 20  # gain
        self.laser_power = 100
        self.thread_active = False
        self.stage_moving = False
        self.thread_to_GUI = queue.Queue()
        self.plots_drawn = [0,0]  # keep track of which plots have been gathered... allows reset once complete
        
        try:        
            self.connect_stage()
            self.checkSerial = QtCore.QTimer()
            self.checkSerial.setSingleShot(False)
            self.checkSerial.timeout.connect(lambda: self.check_serial())
            self.checkSerial.start(100)
        except Exception as e:
            print("Did not connect with stage")
            print(e)
            sys.exit(1)
            
        try:
            self.webcam = cv2.VideoCapture(0)
            self.checkCamera = QtCore.QTimer()
            self.checkCamera.setSingleShot(False)
            self.checkCamera.timeout.connect(lambda: self.display_image())
            self.checkCamera.start(50)
            
        except Exception as e:
            print("Did not connect with webcam")
            print(e)
            sys.exit(1)
        
        try:        
            self.instalise_spectrometer()

        except Exception as e:
            print("Did not connect with spectrometer")
            print(f"Reason: {e}")
            sys.exit(1)

        self.initUI()
        time.sleep(0.2)   
    

    def check_serial(self): # runs on a timer, handles all periodic tasks
        if not self.thread_active:
            if(self.arduino.inWaiting() > 0):
                
                incoming = str(self.arduino.readline().strip())
                if 'moving' in incoming:
                    print("stage move to position ", incoming[9])
                    self.spectraThread = threading.Thread(target=self.get_spectra, name="get spectra", args=(int(incoming[9])-1,1))
                    self.thread_active = True
                    self.spectraThread.start()
                    if sum(self.plots_drawn) == 2: # all plots are already drawn, need to wipe
                        for i in range(2): self.plots[i].getPlotItem().clear()
                        self.plots_drawn = [0,0]
                    
        if self.thread_to_GUI.qsize()>0:
            task = self.thread_to_GUI.get()
            self.display_spectra(task[0],task[1])
            self.thread_active = False
            if sum(self.plots_drawn) == 2: # all plots are already drawn, need to reset LEDs
                self.arduino.write(str.encode("/reset;\n"))


    def instalise_spectrometer(self):
        bus = WasatchBus()

        if bus.is_empty():
            raise RuntimeError("Could not find any spectrometer devices")

        device_id = bus.device_ids[0]
        print("found %s" % device_id)
        
        try:
            device = WasatchDevice(device_id)
            if device is None or not device.connect():
                print("connection failed")
                #sys.exit(1)
            
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
            self.wavenumber = device.settings.wavenumbers[0:-5]
        except Exception as e:
            print("Failed to connect to Wasatch Bus")
            print(e)
            #sys.exit(1)


          
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
               #Setup main Window
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def initUI(self):

        self.setWindowTitle('Outreach Spectrometer GUI')
        sizePolicyMin = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicyMin.setHorizontalStretch(0)
        sizePolicyMin.setVerticalStretch(0)
        screen       =  QtWidgets.QApplication.desktop().screenGeometry().getCoords()
        screenHeight = screen[-1]
        screenWidth  = screen[-2]
        self.setGeometry(0, 0, int(screenWidth*0.8), int(screenHeight*0.8))
        
        
        
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
               #Setup Panes/Tabs
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#OUTPUTs
        #TEXT
        newfont = QtGui.QFont("Times", 90, QtGui.QFont.Bold) 
        
        self.P1                         = QtWidgets.QLabel('1') 
        self.P2                         = QtWidgets.QLabel('2')
        for i in(self.P1,self.P2):
            i.setFont(newfont)
            i.setStyleSheet("border: 3px solid white;")
  
        # graphs
        self.plot_1                    = pg.PlotWidget()
        self.plot_1.setYRange(0,65000)
        self.plot_2                    = pg.PlotWidget()
        self.plot_2.setYRange(0,65000)

        self.plots = [self.plot_1,self.plot_2]
        
        # camera
        self.cameraplot                    = pg.ImageView(view=pg.PlotItem())
        self.cameraplot.ui.roiBtn.hide()
        self.cameraplot.ui.menuBtn.hide()
        self.cameraplot.setLevels(0,225)
#==============================================================================
# Overall assembly
#==============================================================================
        self.WidgetGroup                   = QtWidgets.QGroupBox('')
        self.WidgetGroup.setLayout(QtWidgets.QGridLayout())
        self.WidgetGroup.layout().addWidget(self.plot_1,                     0,8,3,8) 
        self.WidgetGroup.layout().addWidget(self.plot_2,                     3,8,3,8) 
        self.WidgetGroup.layout().addWidget(self.P1,                         0,7,1,1)
        self.WidgetGroup.layout().addWidget(self.P2,                         3,7,1,1)
        self.WidgetGroup.layout().addWidget(self.cameraplot,                 0,0,6,6)               
        self.setCentralWidget(self.WidgetGroup)
               
#==============================================================================
# Spectra Functions
#==============================================================================       

    def normalise(self, _in):
#        assumes a 1 dimensional array (spectra) as input
        # pfit, stats = Polynomial.fit(_in, self.wavenumber, 1, full=True, window=(min(_in), max(_in)),domain=(min(_in), max(_in)))
        # grad, c = pfit
        # for p in range(len(_in)):
        #     pass
#        todo adjust each point using grad and c
 
        scaled = np.interp(_in,(_in.min(),_in.max()),(0,65000))
        kernel = [0.2, 0.2, 0.2, 0.2, 0.2]
        smoothed = np.convolve(scaled, kernel, mode='same')
        return smoothed

#==============================================================================
# Spectrometer Functions
#==============================================================================       

    def get_spectra(self, pos, a): # Runs in thread
        try:
#  wait for stage to finish moving
            print('wait for stage to stop moving')
            while True:
                if(self.arduino.inWaiting() > 0):
                    incoming = str(self.arduino.readline().strip())
                    print(incoming)
                    if 'static' in incoming:
                        print("stage completed move")
                        break
                time.sleep(0.1)
            print('stage stopped moving')
            
            
#  get the spectra
            # DARK
            
            b_spec = np.zeros(self.pixels)
            d_spec = np.zeros(self.pixels)
            l_spec = np.zeros(self.pixels)
            self.dev.hardware.set_laser_enable(False)
            time.sleep(self.integration_time/1000)
            response = self.dev.hardware.get_line().data
            time.sleep(self.integration_time/1000)
            response = self.dev.hardware.get_line().data
            #print(response)
            #print(dir(response))
            #print(type(response.spectrum))
            #print(dir(response.spectrum))
#            sys.stdout.flush()
            d_spec = response.spectrum
            #print("YAY WE DID IT")
            

            # LIGHT
            self.dev.hardware.set_laser_enable(True)
            time.sleep(self.integration_time/1000)
            response = self.dev.hardware.get_line().data
            time.sleep(self.integration_time/1000)
            response = self.dev.hardware.get_line().data
            #response = self.dev.acquire_spectrum()
            
            l_spec = response.spectrum
            self.dev.hardware.set_laser_enable(False)
            
            # SUBTRACT
            d_spec = np.array(d_spec)
            l_spec = np.array(l_spec)
            b_spec = self.normalise(np.subtract(d_spec,l_spec))
            
            #  create progress bar for user comfort
            
            #  add spectra to the right plot in the GUI
            self.thread_to_GUI.put([b_spec,pos])

            
        except Exception as e:
            print(e)        
        return

    
    def set_gain(self, g):  
        self.dev.set_gain(g)
        
    def set_int_time(self, t):  
        self.integration_time = t
        self.dev.hardware.set_integration_time_ms(self.integration_time)
        
    
    def display_spectra(self, spectra, pos):
        
        self.plots_drawn[pos] = 1
        # self.plots[pos].getPlotItem().clear()
        print(len(self.wavenumber))
        print(spectra.shape)
        self.plots[pos].plot(x=self.wavenumber,y=spectra[0:-5])

# =============================================================================
# Camera    
# =============================================================================
    def display_image(self):
        #frame = self.webcam.get_next_data()
        ret, frame = self.webcam.read()
        if not ret:
            self.checkCamera.stop()
            raise RuntimeError("failed to grab frame, stopping timer")
            
        
        image = np.rot90(frame,3) #        image flip (horizontal axis) and rotation (90 deg anti-clockwise)
        image = np.fliplr(image)
        self.cameraplot.setImage(image, autoLevels=False)
        
# =============================================================================
# Arduino Functions
# =============================================================================
    def connect_stage(self):
        self.arduino = serial.Serial(port=stage_address, baudrate=115200, timeout=0.5)
        time.sleep(0.5) #essential to have this delay!
        self.arduino.write(str.encode("/hello;\n"))

        reply = self.arduino.readline().strip()
        print('reply:',reply)
        if reply == b'Dr Raman':
            print('connection established')
            self.arduino.write(str.encode("/reset;\n"))
            
        else:
            print('no connection')
            self.arduino.close()
    
    def closeEvent(self, event): #to do upon GUI being closed
        self.checkSerial.stop()
        self.arduino.close()
        self.dev.disconnect()
        # self.webcam.close()
        


if __name__ == '__main__':

    
    #devices = []
    #for i in range(10):
        #try:
            #cap = cv2.VideoCapture(i)
            #if cap.isOpened():
                #devices.append(i)
                #cap.release()
        #except:
            #pass
    #print("*" * 80)
    #print("DEVICES")
    #print(devices)
    #print("*" * 80)
    app = 0
    app = QtWidgets.QApplication(sys.argv)
    gui = WPSpec()
    gui.show()
    app.exec_()
