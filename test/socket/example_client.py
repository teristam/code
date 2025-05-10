import zmq
import cv2
import numpy as np
import json
import base64
import msgpack
from PyQt6 import QtWidgets, QtCore
import pyqtgraph as pg
import sys
import time


class ImageClient:
    def __init__(self, sub_address="tcp://localhost:5555", push_address="tcp://localhost:5556"):
        self.context = zmq.Context()

        # SUB socket to receive images
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(sub_address)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "image")
        self.image_array = None

        # PUSH socket to send data
        self.push_socket = self.context.socket(zmq.PUSH)
        self.push_socket.connect(push_address)

        print("ImageClient initialized...")

        # UI related 
        self.win = pg.ImageView()
        self.win.show()
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(20)  # update every 100 ms
        # Add a text label to the UI
        self.label = QtWidgets.QLabel("Image Processing Client")
        self.label.setStyleSheet("font-size: 16px; color: white; background-color: black; padding: 5px;")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.status_bar = QtWidgets.QLabel("Status: Ready")
        self.status_bar.setStyleSheet("font-size: 12px; color: white; background-color: gray; padding: 3px;")
        self.status_bar.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.win)
        self.layout.addWidget(self.status_bar)

        self.container = QtWidgets.QWidget()
        self.container.setLayout(self.layout)
        self.container.setMinimumSize(1024, 720)  # Set the minimum width of the window
        self.container.show()

    def receive_image(self):
        if self.sub_socket.poll(timeout=1000):  # Wait for 1 second

            topic, metadata_packed, image_bytes = self.sub_socket.recv_multipart()
            metadata = msgpack.unpackb(metadata_packed)

            # Convert bytes to image array
            img_array = np.frombuffer(image_bytes, dtype=np.uint8).reshape((metadata["height"], metadata["width"]))
            return img_array


    def send_draw_box_message(self, top_left, bottom_right):
        msg = {"DRAW_BOX": {"TOP_LEFT": top_left, "BOTTOM_RIGHT": bottom_right}}
        self.push_socket.send_string(json.dumps(msg))

    def generate_random_box(self, width, height):
        top_left_x = np.random.randint(0, width // 2)
        top_left_y = np.random.randint(0, height // 2)
        bottom_right_x = np.random.randint(width // 2, width)
        bottom_right_y = np.random.randint(height // 2, height)
        return [top_left_x, top_left_y], [bottom_right_x, bottom_right_y]
    
    def process(self, image):
        # Apply a simple Gaussian blur filter to the image
        processed_image = cv2.Canny(image, 100, 200)

        return processed_image
    
    def update(self):
        self.img_array = image_socket.receive_image()

        if self.img_array is None:
            return
        t = time.time()
        processed_image = self.process(self.img_array)
        lapsed = time.time() - t
        self.status_bar.setText(f'Process time: {lapsed*1000:.1f} ms')

        if processed_image is None:
            return
        
        self.win.setImage(processed_image.T, autoLevels=True)  # Transpose if needed for correct orientation
        msg = {"DRAW_BOX": {"TOP_LEFT": 100, "BOTTOM_RIGHT": 200}}
        msg['width'] = processed_image.shape[0]
        msg['height'] = processed_image.shape[1]
        # print('pushing')
        self.push_socket.send_multipart([b'processed', msgpack.packb(msg), processed_image])

        # Generate random coordinates for the box
        # height, width = 100, 100
        # top_left, bottom_right = image_socket.generate_random_box(width, height)
        # # print("Sending message")
        # image_socket.send_draw_box_message(top_left, bottom_right)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    image_socket = ImageClient()
    sys.exit(app.exec())
