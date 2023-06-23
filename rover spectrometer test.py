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
 
        try:        
            self.instalise_spectrometer()

        except Exception as e:
            print("Did not connect with spectrometer")
            print(e)
                
        with open('data.csv') as csvDataFile:
            csvReader = csv.reader(csvDataFile)
            for row in csvReader:
                self.wavenumber.append(float(row[0]))
            self.wavenumber = self.wavenumber[0:self.pixels]
        
        

        self.initUI()
        time.sleep(0.2)   
        self.getSpec = QtCore.QTimer()
        self.getSpec.setSingleShot(False)
        self.getSpec.timeout.connect(lambda: self.get_spectra())
        self.getSpec.start(3000) 
    
    
    
    
        
        
        
        
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


        # graphs
        self.plot_1                    = pg.PlotWidget()
        self.plot_1.setYRange(0,65000)

       
        
#==============================================================================
# Overall assembly
#==============================================================================
        self.WidgetGroup                   = QtGui.QGroupBox('')
        self.WidgetGroup.setLayout(QtGui.QGridLayout())
        self.WidgetGroup.layout().addWidget(self.plot_1,                     0,8,3,8) 


             
        self.setCentralWidget(self.WidgetGroup)
               
#==============================================================================
# Spectra Functions
#==============================================================================       

    def normalise(self, _in):

        scaled = np.interp(_in,(_in.min(),_in.max()),(0,65000))
        kernel = [0.2, 0.2, 0.2, 0.2, 0.2]
        smoothed = np.convolve(scaled, kernel, mode='same')
        return smoothed

#==============================================================================
# Spectrometer Functions
#==============================================================================       

    def get_spectra(self):
        
        self.plot_1.getPlotItem().clear()
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
        
        self.plot_1.plot(x=self.wavenumber,y=b_spec)


 
    def set_gain(self, g):  
        self.dev.set_gain(g)
        
    def set_int_time(self, t):  
        self.integration_time = t
        self.dev.hardware.set_integration_time_ms(self.integration_time)
        
    def closeEvent(self, event): #to do upon GUI being closed
        self.getSpec.stop()
        self.dev.disconnect()


if __name__ == '__main__':
    app = 0
    app = QtGui.QApplication(sys.argv)
    gui = WPSpec()
    gui.show()
    app.exec_()
