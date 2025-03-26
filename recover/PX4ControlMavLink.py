from pymavlink import mavutil
import time
import math

class PX4Control:
    def __init__(self, connection_string="udp:127.0.0.1:60000"):
        """初始化连接"""
        self.connection_string = connection_string
        self.master = None
        self.connect()

    def connect(self):
        """建立与PX4的连接"""
        try:
            self.master = mavutil.mavlink_connection(self.connection_string)
            print("等待心跳信号...")
            self.master.wait_heartbeat()
            print(f"已连接到 {self.connection_string}")
            print(f"心跳信号来自系统 {self.master.target_system} 组件 {self.master.target_component}")
        except Exception as e:
            print(f"连接失败: {str(e)}")
            raise

    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """计算两个点之间的方向角（度）"""
        # 转换为弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # 计算方向角
        d_lon = lon2_rad - lon1_rad
        y = math.sin(d_lon) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
            math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(d_lon)
        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)
        
        # 转换为0-360度
        bearing_deg = (bearing_deg + 360) % 360
        return bearing_deg

    def upload_mission(self, waypoints):
        """上传任务航点，设置机头朝向"""
        try:
            # 发送航点总数
            self.master.mav.mission_count_send(
                self.master.target_system,
                self.master.target_component,
                len(waypoints)
            )

            # 逐个发送航点并计算朝向
            for i, (lat, lon, alt) in enumerate(waypoints):
                msg = self.master.recv_match(type='MISSION_REQUEST', blocking=True)
                if msg.seq != i:
                    print(f"警告: 期望序列 {i}, 收到 {msg.seq}")

                # 计算朝向（如果不是最后一个点，朝向下一个点；如果是最后一个点，保持最后的方向）
                if i < len(waypoints) - 1:
                    next_lat, next_lon, _ = waypoints[i + 1]
                    yaw = self.calculate_bearing(lat, lon, next_lat, next_lon)
                else:
                    # 对于最后一个航点，使用前一段的方向
                    if i > 0:
                        prev_lat, prev_lon, _ = waypoints[i - 1]
                        yaw = self.calculate_bearing(prev_lat, prev_lon, lat, lon)
                    else:
                        yaw = 0.0  # 单个航点时默认朝北

                self.master.mav.mission_item_send(
                    self.master.target_system,
                    self.master.target_component,
                    i,  # sequence
                    mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                    0,  # current (0=not current)
                    1,  # autocontinue
                    0.0,  # param1 (hold time)
                    5.0,  # param2 (accept radius)
                    0.0,  # param3 (pass radius)
                    yaw,  # param4 (yaw angle in degrees)
                    lat,  # latitude
                    lon,  # longitude
                    alt   # altitude
                )

            # 等待MISSION_ACK
            msg = self.master.recv_match(type='MISSION_ACK', blocking=True)
            if msg.type == mavutil.mavlink.MAV_MISSION_ACCEPTED:
                print("任务上传成功")
            else:
                print(f"任务上传失败，错误代码: {msg.type}")

        except Exception as e:
            print(f"上传任务时出错: {str(e)}")
            raise

    def start_mission(self):
        """开始执行任务"""
        try:
            # 切换到AUTO模式
            self.master.set_mode('AUTO')
            
            # 启动任务
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_CMD_MISSION_START,
                0,  # confirmation
                0,  # param1 (first item)
                0,  # param2 (last item)
                0, 0, 0, 0, 0  # unused parameters
            )
            
            print("任务已启动")
            
            # 等待任务开始的确认
            msg = self.master.recv_match(type='COMMAND_ACK', blocking=True)
            if msg and msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                print("任务开始命令被接受")
            else:
                print("任务开始命令失败")

        except Exception as e:
            print(f"启动任务时出错: {str(e)}")
            raise

    def close(self):
        """关闭连接"""
        if self.master:
            self.master.close()
            print("连接已关闭")

def main():
    # 定义航点
    waypoints = [
        (45.4671172, -73.7578372, 6.096),  # 纬度, 经度, 高度（米）
        (45.48382938, -73.73546348, 6.096),
    ]
    
    # 创建PX4Control实例
    px4 = PX4Control("udp:127.0.0.1:60000")
    
    try:
        # 上传任务
        px4.upload_mission(waypoints)
        
        # 等待几秒确保上传完成
        time.sleep(2)
        
        # 开始任务
        px4.start_mission()
        
        # 监控任务状态
        while True:
            msg = px4.master.recv_match(type='MISSION_CURRENT', blocking=True)
            print(f"当前航点序列: {msg.seq}")
            if msg.seq == len(waypoints) - 1:
                print("到达最后一个航点")
                break
            time.sleep(1)
            
    except Exception as e:
        print(f"执行出错: {str(e)}")
    finally:
        # 关闭连接
        px4.close()

if __name__ == "__main__":
    main()