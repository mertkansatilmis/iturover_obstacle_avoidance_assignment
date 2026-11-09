import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from gazebo_msgs.srv import DeleteEntity
import time

class ReactiveObstacleAvoidance(Node):
    def __init__(self):
        super().__init__('reactive_obstacle_avoidance')

        # Launch dosyasından çekilecek parametreler
        self.declare_parameter('max_linear_speed', 0.22)
        self.declare_parameter('min_linear_speed', 0.05)
        self.declare_parameter('max_angular_speed', 0.8)
        self.declare_parameter('safe_distance', 0.75)

        self.max_lin = self.get_parameter('max_linear_speed').value
        self.min_lin = self.get_parameter('min_linear_speed').value
        self.max_ang = self.get_parameter('max_angular_speed').value
        self.safe_dist = self.get_parameter('safe_distance').value

        # Publisher & Subscriber tanımları
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)

        # Gazebo servis istemcisi (/delete_entity) - 60 sn sonra ışığı silmek için
        self.delete_client = self.create_client(DeleteEntity, '/delete_entity')

        self.start_time = time.time()
        self.current_state = "IDLE"
        self.is_terminated = False

        self.get_logger().info("Robot harekete hazir. 60 saniyelik gorev basliyor...")

    def scan_callback(self, msg: LaserScan):
        elapsed = time.time() - self.start_time

        # 60 saniye süre doldu mu kontrolü
        if elapsed >= 60.0 and not self.is_terminated:
            self.stop_and_finish()
            return

        if self.is_terminated:
            return

        # Lidar mesafelerini temizle ve sınırla
        ranges = [r if (r > msg.range_min and r < msg.range_max) else 3.5 for r in msg.ranges]
        
        # Ön bölge (-30 ile +30 derece arası)
        front = min(min(ranges[0:30] + ranges[330:360]), 3.5)
        # Sol bölge (30 ile 90 derece arası)
        left = min(min(ranges[30:90]), 3.5)
        # Sağ bölge (270 ile 330 derece arası)
        right = min(min(ranges[270:330]), 3.5)

        cmd = Twist()

        # Reaktif manevra mantığı (dur-kalk yapmadan yumuşak kaçınma)
        if front < self.safe_dist:
            cmd.linear.x = self.min_lin
            if left > right:
                cmd.angular.z = self.max_ang
                new_state = "Started rotating left."
            else:
                cmd.angular.z = -self.max_ang
                new_state = "Started rotating right."
        elif left < (self.safe_dist * 0.5):
            cmd.linear.x = self.max_lin * 0.7
            cmd.angular.z = -0.35
            new_state = "Adjusting right away from left obstacle."
        elif right < (self.safe_dist * 0.5):
            cmd.linear.x = self.max_lin * 0.7
            cmd.angular.z = 0.35
            new_state = "Adjusting left away from right obstacle."
        else:
            cmd.linear.x = self.max_lin
            cmd.angular.z = 0.0
            new_state = "Moving forward smoothly."

        # Durum değişikliğini logla
        if new_state != self.current_state:
            self.current_state = new_state
            self.get_logger().info(new_state)

        self.cmd_pub.publish(cmd)

    def stop_and_finish(self):
        self.is_terminated = True
        self.get_logger().info("Time limit reached. Stopping...")

        # Robotu durdur
        self.cmd_pub.publish(Twist())

        # /scan aboneliğini iptal et
        self.destroy_subscription(self.scan_sub)
        self.get_logger().info("/scan aboneligi iptal edildi.")

        # Gazebo'daki 'sun' ışığını sil
        if self.delete_client.wait_for_service(timeout_sec=2.0):
            req = DeleteEntity.Request()
            req.name = 'sun'
            self.delete_client.call_async(req)
            self.get_logger().info("Gazebo 'sun' entity silindi, isik kapatildi.")

        # Düğümü sonlandır
        self.destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = ReactiveObstacleAvoidance()
    try:
        rclpy.spin(node)
    except Exception:
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()
