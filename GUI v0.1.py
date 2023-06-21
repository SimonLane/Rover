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
    











if __name__ == '__main__':
    app = 0
    app = QtGui.QApplication(sys.argv)
    gui = Rover()
    gui.show()
    app.exec_()