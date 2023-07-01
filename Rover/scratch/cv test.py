import cv2

cam = cv2.VideoCapture('/dev/video2')
print(cam.isOpened())