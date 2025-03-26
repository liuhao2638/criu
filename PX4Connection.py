
class PX4Connection:
    
    def connect_px4(self):
        # 连接 MAVLink 的逻辑
        print(f"正在连接 MAVLink 实例 {instance_num}")
        try:
            master = mavutil.mavlink_connection(f"udp:127.0.0.1:{60000+instance_num}")
            # print("等待心跳信号...")
            master.wait_heartbeat()
            print(f"已连接到 px4 {instance_num}")
            # print(f"心跳信号来自系统 {master.target_system} 组件 {master.target_component}")
            masters.append(master)
        except Exception as e:
            print(f"连接失败: {str(e)}")
        return masters