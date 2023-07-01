# coding: utf-8
"""
Standard gamepad mappings.

Pulled in to Gamepad.py directly.
"""

class XboxONE(Gamepad):
    fullName = 'Xbox ONE controller'

    def __init__(self, joystickNumber = 0):
        Gamepad.__init__(self, joystickNumber)
        self.axisNames = {
            0: 'LAS -X', #Left Analog Stick Left/Right
            1: 'LAS -Y', #Left Analog Stick Up/Down
            2: 'LT', #Left Trigger
            3: 'RAS -X', #Right Analog Stick Left/Right
            4: 'RAS -Y', #Right Analog Stick Up/Down
            5: 'RT', #Right Trigger
            6: 'DPAD -X', #D-Pad Left/Right
            7: 'DPAD -Y' #D-Pad Up/Down
        }
        self.buttonNames = {
            0:  'A', #A Button
            1:  'B', #B Button
            2:  'X', #X Button
            3:  'Y', #Y Button
            4:  'LB', #Left Bumper
            5:  'RB', #Right Bumper
            6:  'WINDOW', #Hamburger Button
            7:  'MENU', 
            8:  'XBOX', #XBOX Button
            9:  'LASB', #Left Analog Stick button
            10: 'RASB' #Right Analog Stick button
                
        }
        self._setupReverseMaps()

class XboxTWO(Gamepad):
    fullName = 'Xbox TWO controller'

    def __init__(self, joystickNumber = 0):
        Gamepad.__init__(self, joystickNumber)
        self.axisNames = {
            0: 'LAS -X', #Left Analog Stick Left/Right
            1: 'LAS -Y', #Left Analog Stick Up/Down
            2: 'LT', #Left Trigger
            3: 'RAS -X', #Right Analog Stick Left/Right
            4: 'RAS -Y', #Right Analog Stick Up/Down
            5: 'RT', #Right Trigger
            6: 'DPAD -X', #D-Pad Left/Right
            7: 'DPAD -Y' #D-Pad Up/Down
        }
        self.buttonNames = {
            0:  'A', #A Button
            1:  'B', #B Button
            2:  'X', #X Button
            3:  'Y', #Y Button
            4:  'LB', #Left Bumper
            5:  'RB', #Right Bumper
            6:  'WINDOW', #Hamburger Button
            7:  'MENU', 
            8:  'XBOX', #XBOX Button
            9:  'LASB', #Left Analog Stick button
            10: 'RASB' #Right Analog Stick button
                
        }
        self._setupReverseMaps()

class example(Gamepad):
    # This class must have self.axisNames with a map
    # of numbers to capitalised strings. Follow the
    # conventions the other classes use for generic
    # axes, make up your own names for axes unique
    # to your device.
    # self.buttonNames needs the same treatment.
    # Use python Gamepad.py to get the event mappings.
    fullName = 'Enter the human readable name of the device here'

    def __init__(self, joystickNumber = 0):
        Gamepad.__init__(self, joystickNumber)
        self.axisNames = {
            0: 'AXIS0',
            1: 'AXIS1',
            2: 'AXIS2'
        }
        self.buttonNames = {
            0: 'BUTTON0',
            1: 'BUTTON1',
            2: 'BUTTON2'
        }
        self._setupReverseMaps()
