import asyncio
import nest_asyncio

from mavsdk import System
from mavsdk.gimbal import GimbalMode, ControlMode

import time
import math


# 这个类处理mavsdk库控制无人机所需的通用操作
class Drone:
    def __init__(self):
        pass

    def init_mavsdk(self, vehicle):
        # 场景中无人机的属性
        self.vehicle = vehicle

        nest_asyncio.apply()
        # 初始化事件循环
        self.loop = asyncio.get_event_loop()
        # 连接到无人机
        self.loop.run_until_complete(self.connect_drone())

    async def connect_drone(self):

        # 连接单独的mavsdk服务器
        # self.drone = System(
        #     port=self.vehicle.mavsdk_server_port,
        #     sysid=self.vehicle.mavlink_id,
        #     compid=self.vehicle.cam_component_id,
        # )
        self.drone = System(port=self.vehicle.mavsdk_server_port)

        await self.drone.connect(system_address=f"udp://:{self.vehicle.mavlink_api_udp_port_1}")

        # print("Waiting for drone to connect...")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                # print(f"-- Connected to drone!")
                break
        # print("Waiting for drone to have a global position estimate...")
        async for health in self.drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                # print("-- Global position estimate OK")
                break
        print(f"{self.vehicle.vehicle_name} 成功连接")

    # 读取无人机当前位置
    async def get_gps_position(self):
        async for position in self.drone.telemetry.position():
            longitude = position.longitude_deg
            latitude = position.latitude_deg
            altitude = position.absolute_altitude_m
            # print(f"当前位置：纬度 {latitude}, 经度 {longitude}, 海拔 {altitude}米")
            return (latitude, longitude, altitude)

    # 上电，起飞，并稳定
    async def takeoff_and_hold(self):

        print("无人机起飞...")
        while True:
            try:
                await self.drone.action.arm()
                print("上电成功")
                break  # 如果成功执行，则退出循环
            except Exception as e:
                print("上电出错，重试----")
                time.sleep(1)
        await self.drone.action.takeoff()
        await asyncio.sleep(10)

        await self.drone.action.hold()
        print("起飞完成...")

    # 起飞到指定高度（m）
    async def takeoff_and_hold(self, high):
        print("无人机起飞...")
        while True:
            try:
                await self.drone.action.arm()
                print("上电成功")
                break  # 如果成功执行，则退出循环
            except Exception as e:
                print("上电出错，重试----")
                time.sleep(1)
        await self.drone.action.takeoff()
        await asyncio.sleep(5)
        # 获取自身坐标
        (latitude, longitude, altitude) = await self.get_gps_position()
        await self.drone.action.goto_location(latitude, longitude, altitude + high, 0)

    # 读取任务，上传任务，上电无人机，执行任务
    async def exec_mission(self, mission_file):
        # 清除任务
        await self.drone.mission.clear_mission()

        # 读取任务
        self.mission_import_data = await self.drone.mission_raw.import_qgroundcontrol_mission(mission_file)

        # 上传任务
        print(f"{len(self.mission_import_data.mission_items)} mission items imported")
        await self.drone.mission_raw.upload_mission(self.mission_import_data.mission_items)
        print("Mission uploaded")

        while True:
            try:
                await self.drone.action.arm()
                print("上电成功")
                break  # 如果成功执行，则退出循环
            except Exception as e:
                print("上电出错，重试----")
                time.sleep(1)

        await self.drone.mission.start_mission()
        print("Mission started")

    # 查看任务是否完成
    async def is_mission_finished(self):
        return await self.drone.mission.is_mission_finished()

    # 终止任务
    async def stop_mission(self):
        await self.drone.mission.pause_mission()
        await self.drone.mission.clear_mission()

    async def return_to_launch(self):
        # 返航
        await self.drone.action.return_to_launch()

        # 等待返航完成
        async for in_air in self.drone.telemetry.in_air():
            if not in_air:
                print("无人机已降落")
                break

    # 初始化云台状态
    async def init_gimbal(self):
        # 设置云台
        await self.drone.gimbal.take_control(ControlMode.PRIMARY)
        await self.drone.gimbal.set_mode(GimbalMode.YAW_FOLLOW)
        self.yaw_angle = 0  # 云台角度
