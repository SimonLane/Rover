import cv2, time

# codes = [x for x in dir(cv2) if x.startswith("COLOR_")]
# print(codes)

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
        
print('cam ports found:',cam1_port,cam2_port)

cam1 = cv2.VideoCapture(cam1_port)
cam2 = cv2.VideoCapture(cam2_port)

cam1.set(3,320)
cam1.set(4,240)
cam2.set(3,320)
cam2.set(4,240)
to = time.time()

for i in range(5):
    ret, fr1 = cam1.read()
    print(fr1[0][0])

    ret, fr2 = cam2.read()
    print(fr2[0][0])
    
print(time.time() - to)

to = time.time()
for i in range(5):
    cam1.grab()
    cam2.grab()
    
    ret, fr1 = cam1.retrieve()
    print(fr1[0][0])
    ret, fr2 = cam2.retrieve()
    print(fr2[0][0])

print(time.time() - to)