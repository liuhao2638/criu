from pymavlink import mavutil
import time
import math
import multiprocessing
import argparse
# 读取配置文件
import yaml



class PX4Mission:
    def __init__(self,instance_count,base_port):
        self.instance_count = instance_count
        self.base_port = base_port
        self.processes = []
        pass

    def _calculate_bearing(self, lat1, lon1, lat2, lon2):
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

    def start_single_mission(self,instance_num):
        master = mavutil.mavlink_connection(f"udp:127.0.0.1:{self.base_port+instance_num}")
        master.wait_heartbeat()
        # 定义航点
        waypoints = [
            (45.4671172, -73.7578372, 6.096),  # 纬度, 经度, 高度（米）
            (45.48382938, -73.73546348, 6.096),
        ]
        # 任务上传
        master.mav.mission_count_send(
            master.target_system,
            master.target_component,
            len(waypoints)
        )
        # 逐个发送航点并计算朝向
        for i, (lat, lon, alt) in enumerate(waypoints):
 
            # 计算朝向（如果不是最后一个点，朝向下一个点；如果是最后一个点，保持最后的方向）
            if i < len(waypoints) - 1:
                next_lat, next_lon, _ = waypoints[i + 1]
                yaw = self._calculate_bearing(lat, lon, next_lat, next_lon)
            else:
                # 对于最后一个航点，使用前一段的方向
                if i > 0:
                    prev_lat, prev_lon, _ = waypoints[i - 1]
                    yaw = self._calculate_bearing(prev_lat, prev_lon, lat, lon)
                else:
                    yaw = 0.0  # 单个航点时默认朝北

            master.mav.mission_item_send(
                master.target_system,
                master.target_component,
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
            # print(yaw,lat,lon,alt)

        # 等待MISSION_ACK
        msg = master.recv_match(type='MISSION_ACK', blocking=True)
        
        # 等待几秒确保上传完成
        time.sleep(1)
        
        # 开始任务
        # 切换到MISSION模式
        master.set_mode('MISSION')
        
        # 启动任务
        master.mav.command_long_send(
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_CMD_MISSION_START,
            0,  # confirmation
            0,  # param1 (first item)
            0,  # param2 (last item)
            0, 0, 0, 0, 0  # unused parameters
        )

        # 等待任务开始的确认
        # msg = master.recv_match(type='COMMAND_ACK', blocking=True)
        
        master.close()
        print(f"第{instance_num}架px4开始任务")

    def start_multiple_mission(self):
        instances = list(range(self.instance_count))

        # 并行执行计算得分函数
        with multiprocessing.Pool() as pool:
            pool.map(self.start_single_mission, instances)
            # pool.join()   # 等待所有任务完成        

def main():
    with open("./Cptool/config.yaml", "r") as f:
        config = yaml.load(f.read(), Loader=yaml.FullLoader)
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser()

    # 添加参数
    parser.add_argument("--instance_count", type=int, help="实例个数", default=config["simulation"]["instance_count"])

    # 解析参数
    args = parser.parse_args()
        
    # 创建PX4Mission实例
    px4 = PX4Mission(args.instance_count,config["simulation"]["connect_port_1"])
    # 开始执行任务
    
    px4.start_multiple_mission()
    # px4.start_single_mission(299)
    
    


if __name__ == "__main__":
    main()