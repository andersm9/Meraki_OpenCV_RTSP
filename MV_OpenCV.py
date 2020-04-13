#!/usr/bin/env python

# USAGE
# python real_time_object_detection.py

import sys
import configparser
import time
import numpy as np
import imutils
import cv2
import paho.mqtt.client as mqttClient

### Gather configuration parameters
def gather_arg():

    conf_par = configparser.ConfigParser()
    try:
        conf_par.read('credentials.ini')
        host= conf_par.get('camera', 'host')
        broker = conf_par.get('mqtt', 'broker')
        port = conf_par.getint('mqtt', 'port')
        prototxt = conf_par.get('ssd', 'prototxt')
        model = conf_par.get('ssd', 'model')
        conf = conf_par.getfloat('ssd', 'conf')
    except:
        print('Missing credentials or input file!')
        sys.exit(2)
    return host, broker, port, prototxt, model, conf

### connect to MQTT Broker ###
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")
        global Connected                #Use global variable
        Connected = True                #Signal connection
    else:
        print("Connection failed")
(host, broker, port, prototxt, model, conf) = gather_arg()

Connected = False   #global variable for the state of the connection
client = mqttClient.Client("Python")               #create new instance
client.on_connect= on_connect                      #attach function to callback
client.connect(broker, port=port)          #connect to broker
client.loop_start()        #start the loop
while Connected != True:    #Wait for connection
    time.sleep(1.0)


# initialize the list of class labels MobileNet SSD was trained to
# detect, then generate a set of bounding box colors for each class
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
    "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
    "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
    "sofa", "train", "tvmonitor"]
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

# load our serialized model from disk
print("[INFO] loading model...")
#net = cv2.dnn.readNetFromCaffe(args["prototxt"], args["model"])
net = cv2.dnn.readNetFromCaffe(prototxt, model)

# initialize the video stream, allow the cammera sensor to warmup,
print("[INFO] starting video stream...")

#if args["source"] == "webcam":
	#vs = cv2.VideoCapture('rtsp://192.168.128.29:9000/live')
vs = cv2.VideoCapture(host)
time.sleep(2.0)

detected_objects = []
# loop over the frames from the video stream
while True:
    # grab the frame from the threaded video stream and resize it
    # to have a maximum width of 400 pixels
    #if args["source"] == "webcam":
        #ret, frame = vs.read()
    ret, frame = vs.read()

    #else:
        #imgResp=urlopen(url)
        #imgNp=np.array(bytearray(imgResp.read()),dtype=np.uint8)
        #frame=cv2.imdecode(imgNp,-1)

    frame = imutils.resize(frame, width=800)

    # grab the frame dimensions and convert it to a blob
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
        0.007843, (300, 300), 127.5)

    # pass the blob through the network and obtain the detections and
    # predictions
    net.setInput(blob)
    detections = net.forward()

    # loop over the detections
    for i in np.arange(0, detections.shape[2]):
        # extract the confidence (i.e., probability) associated with
        # the prediction
        confidence = detections[0, 0, i, 2]

        # filter out weak detections by ensuring the `confidence` is
        # greater than the minimum confidence
        if confidence > conf:
            # extract the index of the class label from the
            # `detections`, then compute the (x, y)-coordinates of
            # the bounding box for the object
            idx = int(detections[0, 0, i, 1])
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            # draw the prediction on the frame
            label = "{}: {:.2f}%".format(CLASSES[idx],
                confidence * 100)
            print(label)
            client.publish("python/test",label)


            detected_objects.append(label)
            cv2.rectangle(frame, (startX, startY), (endX, endY),
                COLORS[idx], 2)
            y = startY - 15 if startY - 15 > 15 else startY + 15
            cv2.putText(frame, label, (startX, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)

    # show the output frame
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break

#cleanup
cv2.destroyAllWindows()

