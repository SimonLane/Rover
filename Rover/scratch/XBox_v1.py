# HC OSIRIS Rover Comms + Sound + Change Modes + Override Control + Deadman Switch + Emergency Shutdown

from datetime import datetime
import time

# ========== 1. Serial commands to Teensy ==========
import serial

# Serial parameters
baud_rate = 115200
wheel_teensy_port ='/dev/ttyACM0'
arm_teensy_port = '/dev/ttyACM1'

# Basic read and write to microcontrollers
def teensy_write (port, rate, message_string):
    ser = serial.Serial(port,rate)
    ser.write(message_string.encode())
    print ("Message sent to Teensy:", message_string)
    
def teensy_read (port, rate):
    ser = serial.Serial(port,rate)
    response = ser.readline().decode().strip()
    print ("Response from Teensy:", response)
    return response



# Test handling x and y positions and send to Teensy
def teensy_wheel_xy (port,rate, joy_X, joy_Y):
    #ser = serial.Serial(port,rate)
   
    #velocity_command = f"/speed.{joy_X}.{joy_Y}.0;"
    velocity_command = f"/join.{joy_X}.{joy_Y}.0;"
    #ser.write(velocity_command.encode())
    print ("Message sent to WHEELS:", velocity_command)
    
    #response = ser.readline().decode().strip()
    #print ("WHEELS Respond:", response)
    #return response
    
def teensy_arm_xy (port,rate, joy_X, joy_Y):
    #ser = serial.Serial(port,rate)
    
    #position_command = f"/position.{joy_X}.{joy_Y}.0;"
    position_command = f"/add.{joy_X}.{joy_Y}.0;"
    #ser.write(position_command.encode())
    print ("Message sent to ARMS:", position_command)
    
    #response = ser.readline().decode().strip()
    #print ("ARMS Respond:", response)
    #return response

def teensy_wrist_xy (port,rate, joy_X, joy_Y):
    #ser = serial.Serial(port,rate)
    
    #position_command = f"/position.{joy_X}.{joy_Y}.0;"
    position_command = f"/add.{joy_X}.{joy_Y}.0;"
    #ser.write(position_command.encode())
    print ("Message sent to WRIST:", position_command)
    
    #response = ser.readline().decode().strip()
    #print ("WRIST Responds:", response)
    #return response

# ========== 2. Pygame to access the Xbox One Controller ==========
import pygame
from pygame.constants import JOYBUTTONDOWN
from pygame.constants import JOYBUTTONUP
from pygame.constants import JOYHATMOTION
from pygame.constants import JOYAXISMOTION


# Start pygame
pygame.init()

# ========== 4. Initialise Both Demonstrator and Pilot Controllers ==========
# Count how many controllers connected
jy = pygame.joystick.Joystick
playerno = pygame.joystick.get_count()
print ("No. of controllers =", playerno)

# Initialise controllers and get feedback
player_list = []
for i in range (0,playerno):
    player_list.append(jy(i))
    # Make sure each controller gets initialised
    player_list[-1].init()
    # Print out the name of the controllers
    print (f"Controller {jy(i).get_instance_id()} =", jy(i).get_name())
    # Rumble for 500 ms to confirm initialisation
    jy(i).rumble(0.5,0.9,500)
    time.sleep(0.01)

# Ready to go
print ("Ready for Input Test")


# ========== 5. Main Communications Loop ==========

def mission_control():
    # Initialise selected mode to None
    rover_mode = None

    # Initiate x and y right joystick positions: arm and wheel
    x_rwheel_pos = 0
    y_rwheel_pos = 0
    
    x_rarm_pos = 0
    y_rarm_pos = 0
    
    # Intiate x and y left joystick positions: wrist
    x_lwrist_pos = 0
    y_lwrist_pos = 0

    # Initiate mode: 0 = standby, 1 = wheel, 2 = arm, 3 = raman
    rover_mode = 0
    
    # Initiate pilot mode: True = console controls, False = demonstrator controls
    pilot_enabled = True
    
    # Initiate laser mode: True = interlock open, False = interlock closed
    laser_enabled = True
    
    # Initiate Emergency Stop 2-step
    e_stop_lb = False
    e_stop_rb = False
    
    # Start the main operating loop
    running = True

    # Looking for button press and joystick movement events
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Face Button Events (A,B,X,Y,LB,RB,View,Menu,Xbox,LS,RS,Share)
            # Button press event
            if event.type ==JOYBUTTONDOWN:
                for p, player in enumerate(player_list):
                    if event.joy == p:
                        if event.button == 2: #X
                            rover_mode = 1 #wheel
                            print (f"---------- Now in Wheel Mode (X) triggered by {jy(p).get_name()} ---------- ")
#                             
                        if event.button == 0: #A
                            rover_mode = 2 #arm
                            print (f"---------- Now in Arm Mode (B) triggered by {jy(p).get_name()} ---------- ")
#                            
                        if event.button == 1: #B
                            rover_mode = 3 #raman
                            print (f"---------- Now in Raman Mode (X) triggered by {jy(p).get_name()} ---------- ")
#                            
                        if event.button == 3: #Y
                            # Change whether pilot is enabled; switch with each button press
                            if pilot_enabled:
                                pilot_enabled = False
                                print ("---------- Taking Control from Pilot ----------")
                            else:
                                pilot_enabled = True
                                print ("---------- Restoring Control to Pilot ----------")
                            jy(p).rumble(0.9,0.9,500) # Rumble to confirm
                                
                        if event.button == 4: #LB
                            e_stop_lb = True
                            print (f"---------- EMERGENCY STOP: Hold LB + Press RB on {jy(p).get_name()} ----------")
                            jy(p).rumble(0.9,0.9,500) # Rumble to confirm
                            
                        if event.button == 5: #RB
                            e_stop_rb = True
                            print (f"---------- EMERGENCY STOP: Hold RB + Press LB on {jy(p).get_name()} ----------")                            
                            jy(p).rumble(0.9,0.9,500) # Rumble to confirm
                            
            if event.type ==JOYBUTTONUP:
                for p, player in enumerate(player_list):
                    if event.joy == p:
                        if event.button == 4: #LB
                            e_stop_lb = False
                            print (f"---------- EMERGENCY STOP: ABORTED by {jy(p).get_name()} ----------")
                        
                        if event.button == 5:
                            e_stop_rb = False #RB
                            print (f"---------- EMERGENCY STOP: ABORTED by {jy(p).get_name()} ----------")
                            
            
            # Joysticks and Triggers Events (Analogue)
            elif event.type ==JOYAXISMOTION:
                              
                for p, player in enumerate(player_list):
                    if event.joy == p:
                        
                        # Start programme in STANDBY mode
                        if rover_mode == 0:
                            print (f" STANDBY: Ignoring all joysticks, {jy(p).get_name()}! Choose Mode: Wheel (X) or Arm (A)")
                            
                        # WHEEL mode
                        if rover_mode == 1: #
                            if pilot_enabled == True:
                                if jy(p).get_name() == "Xbox Adaptive Controller":
                                    if event.axis == 3: # Right Stick L/R
                                        x_rwheel_pos = int(1000*event.value)
                                        
                                    elif event.axis == 4: # Right Stick U/D
                                        y_rwheel_pos = int(1000*event.value)
                                        
                                    teensy_wheel_xy(wheel_teensy_port,baud_rate, x_rwheel_pos, y_rwheel_pos)
                                
                                else:
                                    print (f"WHEEL: IGNORING you Demonstrator on {jy(p).get_name()}")
                            
                            else:
                                if jy(p).get_name() == "Xbox Adaptive Controller":
                                    print (f"WHEEL: IGNORING you Pilot on {jy(p).get_name()}")
                                
                                else: # If Pilot not enabled
                                    if event.axis == 3: # Right Stick L/R
                                        x_rwheel_pos = int(1000*event.value)

                                    elif event.axis == 4: # Right Stick U/D
                                        y_rwheel_pos = int(1000*event.value)

                                    teensy_wheel_xy(wheel_teensy_port,baud_rate, x_rwheel_pos, y_rwheel_pos)
                                    
                        # ARM mode
                        if rover_mode == 2:
                            if pilot_enabled == True:                            
                                if jy(p).get_name()  == "Xbox Adaptive Controller":
                                    if event.axis == 3: # Right Stick L/R
                                        x_rarm_pos = int(1000*event.value)

                                    elif event.axis == 4: # Right Stick U/D
                                        y_rarm_pos = int(1000*event.value)

                                    teensy_arm_xy (arm_teensy_port,baud_rate, x_rarm_pos, y_rarm_pos)
                                    #print (f"ARM Right Joystick, x = {x_rarm_pos}, y = {y_rarm_pos}")
                                
                                else:
                                    print (f"ARM: IGNORING you Demonstrator on {jy(p).get_name()}")
                            else: # If pilot not enabled
                                if jy(p).get_name()  == "Xbox Adaptive Controller":
                                    print (f"ARM: IGNORING you Pilot on {jy(p).get_name()}")
                                
                                else:
                                    if event.axis == 3: # Right Stick L/R
                                        x_rarm_pos = int(1000*event.value)
                                        
                                    elif event.axis == 4: # Right Stick U/D
                                        y_rarm_pos = int(1000*event.value)
                                                                    
                                    elif event.axis == 0: # Left Stick L/R
                                        x_lwrist_pos = int(1000*event.value)

                                    elif event.axis == 1: # Left Stick U/D
                                        y_lwrist_pos = int(1000*event.value)
                                    
                                    teensy_arm_xy (arm_teensy_port,baud_rate, x_rarm_pos, y_rarm_pos)
                                    #print (f"ARM Right Joystick, x = {x_rarm_pos}, y = {y_rarm_pos}")                            
                                    print (f"WRIST Left Joystick, x = {x_lwrist_pos}, y = {y_lwrist_pos}")                                    
                                   
                                
                        # Raman mode
                        if rover_mode == 3:                               
                            # Deadman Switch for Laser - only when trigger fully pressed
                            if  event.axis == 5: #Right Trigger
                                if event.value == 1.0:
                                    print (f"Deadman Switch Engaged ({event.value}): INTERLOCK OPEN")
                                    time.sleep(0.25)            
                                    print("3...")
                                    time.sleep(0.25)
                                    print("2...")
                                    time.sleep(0.25)
                                    print("1...")
                                    time.sleep(0.25)
                                    # Rumble to confirm
                                    jy(p).rumble(0.5,0.9,500)
                                else:
                                    print (f"Deadman Switch Not Yet Engaged ({event.value}): INTERLOCK CLOSED")                            
                            else:
                                print (f"RAMAN: Ignoring Joysticks")
                                #print (f" RAMAN: Ignoring Right Joystick, {jy(p).get_name()} whilst laser firing")                                
            
        
        # Emergency Stop Protocol: Press RB + LB Together
        if e_stop_lb and e_stop_rb == True:
            # Rumble to confirm
            jy(p).rumble(0.5,0.9,500)
            print ("---------- SHUTTING DOWN ----------")
            time.sleep(0.25)            
            print("3...")
            time.sleep(0.25)
            print("2...")
            time.sleep(0.25)
            print("1...")
            time.sleep(0.25)
            pygame.quit()
            
# Start main loop
mission_control()