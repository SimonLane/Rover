# -*- coding: utf-8 -*-
"""
Outreach Spectrometer GUI


@author: Simon Lane
"""

#imports
from wasatch.WasatchBus    import WasatchBus
from wasatch.WasatchDevice import WasatchDevice


from PyQt5 import QtGui, QtCore, Qt
import sys, time, serial, glob
import pyqtgraph as pg
import numpy as np
Polynomial = np.polynomial.Polynomial
import csv, threading, queue
import imageio as iio



from usb.backend import libusb1

stage_address = "/dev/cu.usbmodem14201"

class WPSpec(QtGui.QMainWindow):
    def __init__(self):
        super(WPSpec, self).__init__()
        
        
        #test data
        self.spectra = []
        self.wavenumber = []
        self.pixels=1952
        self.HOST_TO_DEVICE=0x40
        self.DEVICE_TO_HOST=0xC0
        self.BUFFER_SIZE = 8
        self.integration_time = 500 #integration time
        self.averages = 2
        self.gain = 20  # gain
        self.laser_power = 100
        self.thread_active = False
        self.stage_moving = False
        self.thread_to_GUI = queue.Queue()
        self.plots_drawn = [0,0,0,0]  # keep track of which plots have been gathered... allows reset once complete
        
        try:        
            self.connect_stage()
            self.checkSerial = QtCore.QTimer()
            self.checkSerial.setSingleShot(False)
            self.checkSerial.timeout.connect(lambda: self.check_serial())
            self.checkSerial.start(100)
            
            
            self.webcam = iio.get_reader("<video1>")
            self.checkCamera = QtCore.QTimer()
            self.checkCamera.setSingleShot(False)
            self.checkCamera.timeout.connect(lambda: self.display_image())
            self.checkCamera.start(50)
            
        except Exception as e:
            print("Did not connect with stage")
            print(e)
        
        try:        
            self.instalise_spectrometer()

        except Exception as e:
            print("Did not connect with spectrometer")
            print(e)
                
        with open('data.csv') as csvDataFile:
            csvReader = csv.reader(csvDataFile)
            for row in csvReader:
                self.wavenumber.append(float(row[0]))
            self.wavenumber = self.wavenumber[0:1947]
        
        

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
                    if sum(self.plots_drawn) == 4: # all plots are already drawn, need to wipe
                        for i in range(4): self.plots[i].getPlotItem().clear()
                        self.plots_drawn = [0,0,0,0]
                    
        if self.thread_to_GUI.qsize()>0:
            task = self.thread_to_GUI.get()
            self.display_spectra(task[0],task[1])
            self.thread_active = False
            if sum(self.plots_drawn) == 4: # all plots are already drawn, need to reset LEDs
                self.arduino.write(str.encode("/reset;\n"))
    
        
        
        
        
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
        self.wavenumbers = device.settings.wavenumbers[0:-5]


          
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
               #Setup main Window
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def initUI(self):

        self.setWindowTitle('Outreach Spectrometer GUI')
#        palette = QtGui.QPalette()
#        palette.setColor(QtGui.QPalette.Background, QtGui.QColor(80,80,80))
#        self.setPalette(palette)
        
        sizePolicyMin = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicyMin.setHorizontalStretch(0)
        sizePolicyMin.setVerticalStretch(0)
        screen       =  QtGui.QApplication.desktop().screenGeometry().getCoords()
        screenHeight = screen[-1]
        screenWidth  = screen[-2]
        self.setGeometry(0, 0, screenWidth*0.8, screenHeight*0.8)
        
        
        
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
               #Setup Panes/Tabs
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#OUTPUTs
        #TEXT
        newfont = QtGui.QFont("Times", 90, QtGui.QFont.Bold) 
        
        self.P1                         = QtGui.QLabel('1') 
        self.P2                         = QtGui.QLabel('2')
        self.P3                         = QtGui.QLabel('3')
        self.P4                         = QtGui.QLabel('4')
        for i in(self.P1,self.P2,self.P3,self.P4):
            i.setFont(newfont)
            i.setStyleSheet("border: 3px solid white;")
  
        # graphs
        self.plot_1                    = pg.PlotWidget()
        self.plot_1.setYRange(0,65000)
        self.plot_2                    = pg.PlotWidget()
        self.plot_2.setYRange(0,65000)
        self.plot_3                    = pg.PlotWidget()
        self.plot_3.setYRange(0,65000)
        self.plot_4                    = pg.PlotWidget()
        self.plot_4.setYRange(0,65000)
        self.plots = [self.plot_1,self.plot_2,self.plot_3,self.plot_4]
        
        # camera
        self.cameraplot                    = pg.ImageView(view=pg.PlotItem())
        self.cameraplot.ui.roiBtn.hide()
        self.cameraplot.ui.menuBtn.hide()
        self.cameraplot.setLevels(0,125)
#==============================================================================
# Overall assembly
#==============================================================================
        self.WidgetGroup                   = QtGui.QGroupBox('')
        self.WidgetGroup.setLayout(QtGui.QGridLayout())
        self.WidgetGroup.layout().addWidget(self.plot_1,                     0,8,3,8) 
        self.WidgetGroup.layout().addWidget(self.plot_2,                     3,8,3,8) 
        self.WidgetGroup.layout().addWidget(self.plot_3,                     6,8,3,8) 
        self.WidgetGroup.layout().addWidget(self.plot_4,                     9,8,3,8) 
        self.WidgetGroup.layout().addWidget(self.P1,                         0,7,1,1)
        self.WidgetGroup.layout().addWidget(self.P2,                         3,7,1,1)
        self.WidgetGroup.layout().addWidget(self.P3,                         6,7,1,1)
        self.WidgetGroup.layout().addWidget(self.P4,                         9,7,1,1)
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
            
            # SUBTRACT
            d_spec = np.array(d_spec)
            l_spec = np.array(l_spec)
            b_spec = self.normalise(np.subtract(l_spec,d_spec))
            
            #  create progress bar for user comfort
            
            #  add spectra to the right plot in the GUI
            # self.thread_to_GUI.put([d_spec,pos])
            # self.thread_to_GUI.put([l_spec,pos])
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
        self.plots[pos].plot(x=self.wavenumber,y=spectra[0:-5])

# =============================================================================
# Camera    
# =============================================================================
    def display_image(self):
        frame = self.webcam.get_next_data()
        
        image = np.rot90(frame,3) #        image flip (horizontal axis) and rotation (90 deg anti-clockwise)
        image = np.fliplr(image)
        self.cameraplot.setImage(image, autoLevels=False)
        
# =============================================================================
# Arduino Functions
# =============================================================================
    def connect_stage(self):
        self.arduino = serial.Serial(port=stage_address, baudrate=115200, timeout=0.5)
        time.sleep(1) #essential to have this delay!
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
    app = 0
    app = QtGui.QApplication(sys.argv)
    gui = WPSpec()
    gui.show()
    app.exec_()
