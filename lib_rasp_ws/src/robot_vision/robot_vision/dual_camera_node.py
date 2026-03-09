import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
import cv2
import numpy as np

class DualCameraNode(Node):
    def __init__(self):
        super().__init__('dual_camera_node')
        
        # 1. 물리적 포트 경로 
        # 로봇팔 카메라 (이제 Port 1.1 위치를 arm으로 할당)
        arm_path = '/dev/v4l/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.1:1.0-video-index0'
        self.cap_arm = cv2.VideoCapture(arm_path)
        self.cap_arm.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap_arm.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.cap_arm.set(cv2.CAP_PROP_FPS, 30)
        self.cap_arm.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

        # 로봇 하단 카메라 (이제 Port 1.2 위치를 base로 할당)
        base_path = '/dev/v4l/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.2:1.0-video-index0'
        self.cap_base = cv2.VideoCapture(base_path)
        self.cap_base.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap_base.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.cap_base.set(cv2.CAP_PROP_FPS, 15)
        self.cap_base.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        
        # 2. 퍼블리셔 설정
        self.pub_arm = self.create_publisher(CompressedImage, '/camera_arm/image_raw/compressed', 10)
        self.pub_base = self.create_publisher(CompressedImage, '/camera_base/image_raw/compressed', 10)
        
        self.jpeg_quality = 80 
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info('--- [듀얼 카메라 연결: Arm(1.1), Base(1.2)] ---')

    def timer_callback(self):
        # 로봇팔 카메라 처리
        ret_arm, frame_arm = self.cap_arm.read()
        if ret_arm:
            self.publish_compressed(frame_arm, self.pub_arm)

        # 로봇 하단 카메라 처리
        ret_base, frame_base = self.cap_base.read()
        if ret_base:
            self.publish_compressed(frame_base, self.pub_base)

    def publish_compressed(self, frame, publisher):
        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.format = "jpeg"
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        result, encimg = cv2.imencode('.jpg', frame, encode_param)
        if result:
            msg.data = np.array(encimg).tobytes()
            publisher.publish(msg)

    def __del__(self):
        if hasattr(self, 'cap_arm'): self.cap_arm.release()
        if hasattr(self, 'cap_base'): self.cap_base.release()

def main(args=None):
    rclpy.init(args=args)
    node = DualCameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down Dual Camera Node...')
    finally:
        node.cap_arm.release()
        node.cap_base.release()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()