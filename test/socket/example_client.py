import zmq
import cv2
import numpy as np
import json
import base64
import msgpack
from PyQt6 import QtWidgets
import pyqtgraph as pg
import sys

class ImageClient:
    def __init__(self, sub_address="tcp://localhost:5555", push_address="tcp://localhost:5556"):
        self.context = zmq.Context()

        # SUB socket to receive images
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(sub_address)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        # PUSH socket to send data
        self.push_socket = self.context.socket(zmq.PUSH)
        self.push_socket.connect(push_address)

        print("ImageClient initialized...")

    def receive_image(self):
        if self.sub_socket.poll(timeout=1000):  # Wait for 1 second

            topic, metadata_packed, image_bytes = self.sub_socket.recv_multipart()
            metadata = msgpack.unpackb(metadata_packed)
            print(metadata)
            print(topic)

            if topic == b'image':  # Filter by topic
                # Convert bytes to image array
                img_array = np.frombuffer(image_bytes, dtype=np.uint8).reshape((metadata["height"], metadata["width"]))
                return img_array
            else:
                return None

    def send_draw_box_message(self, top_left, bottom_right):
        msg = {"DRAW_BOX": {"TOP_LEFT": top_left, "BOTTOM_RIGHT": bottom_right}}
        self.push_socket.send_string(json.dumps(msg))

    def generate_random_box(self, width, height):
        top_left_x = np.random.randint(0, width // 2)
        top_left_y = np.random.randint(0, height // 2)
        bottom_right_x = np.random.randint(width // 2, width)
        bottom_right_y = np.random.randint(height // 2, height)
        return [top_left_x, top_left_y], [bottom_right_x, bottom_right_y]


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = pg.ImageView()
    win.show()
    image_socket = ImageClient()
    timer = pg.QtCore.QTimer()
    def update():
        img_array = image_socket.receive_image()
        # print(img_array)
        if img_array is not None:
            win.setImage(img_array.T, autoLevels=True)  # Transpose if needed for correct orientation

        # Generate random coordinates for the box
        height, width = 100, 100
        top_left, bottom_right = image_socket.generate_random_box(width, height)
        # print("Sending message")
        image_socket.send_draw_box_message(top_left, bottom_right)

    timer.timeout.connect(update)
    timer.start(100)  # update every 100 ms

    sys.exit(app.exec())
