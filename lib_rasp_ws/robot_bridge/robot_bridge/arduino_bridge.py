import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
import serial
import sys

class ArduinoBridge(Node):
    def __init__(self):
        super().__init__('arduino_bridge')
        
        # 시리얼 설정 (포트 확인: /dev/ttyUSB0 또는 /dev/ttyACM0)
        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.1)
            self.get_logger().info('아두이노 연결 성공 (통합 주행 모드)')
        except Exception as e:
            self.get_logger().error(f'연결 실패: {e}')
            sys.exit()
        
        self.wheel_sub = self.create_subscription(Twist, '/lib_cmd_vel', self.wheel_callback, 10)
        self.arm_sub = self.create_subscription(String, '/arm_command', self.arm_callback, 10)

    def wheel_callback(self, msg):
        vx = msg.linear.x
        az = msg.angular.z
        
        base_pwm = 35     # 기본 주행 속도
        accel_gain = 55   # 가속 비례 가중치 (az가 0.2일 때 약 11만큼 더 가속)
        spin_pwm = 30     # 제자리 회전 속도

        # 1. 완전 정지
        if abs(vx) < 0.05 and abs(az) < 0.05:
            cmd = "x\n"
        
        # 2. 주행 중 보정 (가속형 비례 제어 - Arc Turn)
        elif abs(vx) > 0.05:
            l_spd = base_pwm
            r_spd = base_pwm
            
            if az > 0.05:    # 좌회전: 오른쪽 바퀴 가속
                r_spd += int(abs(az) * accel_gain)
            elif az < -0.05: # 우회전: 왼쪽 바퀴 가속
                l_spd += int(abs(az) * accel_gain)
            
            # 후진 시 방향 반전
            if vx < 0:
                l_spd, r_spd = -l_spd, -r_spd
            
            cmd = f"v:{l_spd}:{r_spd}\n"

        # 3. 정지 상태에서 정렬 (상반 회전 - Spin Turn)
        else:
            if az > 0: # 제자리 좌회전 (왼쪽 후진, 오른쪽 전진)
                cmd = f"v:{-spin_pwm}:{spin_pwm}\n"
            else:      # 제자리 우회전 (왼쪽 전진, 오른쪽 후진)
                cmd = f"v:{spin_pwm}:{-spin_pwm}\n"
        
        self.ser.write(cmd.encode())
        self.get_logger().info(f'전송 명령: {cmd.strip()}')

    def arm_callback(self, msg):
        # 팔 명령 전송
        self.ser.write((msg.data + "\n").encode())
        self.get_logger().info(f'전송 팔 명령: {msg.data}')

def main(args=None):
    rclpy.init(args=args)
    node = ArduinoBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()