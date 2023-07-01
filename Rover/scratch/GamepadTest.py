import Gamepad, time


pollInterval = 0.05
XAC = Gamepad.XboxONE
X1C = Gamepad.XboxTWO
buttonHappy = 'A'
buttonBeep = 'B'
buttonExit = 'Y'
joystickSpeed = 'RAS -Y'
joystickSteering = 'RAS -X'

# Wait for a connection
if not Gamepad.available():
    print('Please connect your gamepad...')
    while not Gamepad.available():
        time.sleep(1.0)
gamepad1 = XAC(joystickNumber=0)
print('Gamepad 1 connected')
if not Gamepad.available():
    print('Please connect your gamepad...')
    while not Gamepad.available():
        time.sleep(1.0)
gamepad2 = X1C(joystickNumber=1)
print('Gamepad 2 connected')

# Set some initial state
global running
global beepOn
global speed
global steering
running = True
beepOn = False
speed = 0.0
steering = 0.0

# Create some callback functions
def happyButtonPressed():
    print(':)')

def happyButtonReleased():
    print(':(')

def beepButtonChanged(isPressed):
    global beepOn
    beepOn = isPressed

def exitButtonPressed():
    global running
    print('EXIT')
    running = False

def speedAxisMoved2(position):
    global speed
    speed = -position   # Inverted

def steeringAxisMoved2(position):
    global steering
    steering = position # Non-inverted

gamepad1.startBackgroundUpdates()
gamepad2.startBackgroundUpdates()

# Register the callback functions
gamepad1.addButtonPressedHandler(buttonHappy, happyButtonPressed)
gamepad1.addButtonReleasedHandler(buttonHappy, happyButtonReleased)
gamepad1.addButtonChangedHandler(buttonBeep, beepButtonChanged)
gamepad1.addButtonPressedHandler(buttonExit, exitButtonPressed)

# Register the callback functions
gamepad2.addButtonPressedHandler(buttonHappy, happyButtonPressed)
gamepad2.addButtonReleasedHandler(buttonHappy, happyButtonReleased)
gamepad2.addButtonChangedHandler(buttonBeep, beepButtonChanged)
gamepad2.addButtonPressedHandler(buttonExit, exitButtonPressed)
gamepad2.addAxisMovedHandler(joystickSpeed, speedAxisMoved2)
gamepad2.addAxisMovedHandler(joystickSteering, steeringAxisMoved2)

# Keep running while joystick updates are handled by the callbacks
try:
    while running:
        # Show the current speed and steering
        print('%+.1f %% speed, %+.1f %% steering__1' % (speed * 100, steering * 100))

        # Display the beep if held
        if beepOn:
            print('1BEEP')

            # Sleep for our polling interval
        time.sleep(pollInterval)
finally:
    # Ensure the background thread is always terminated when we are done
    gamepad1.disconnect()
    gamepad2.disconnect()