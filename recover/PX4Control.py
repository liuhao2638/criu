import asyncio
from mavsdk import System

import multiprocessing
import argparse

class PX4Control:
    def __init__(self):
        pass
        
    async def connect(self,instance_num):
        drone = System(port=70000+instance_num)
        await drone.connect(system_address=60000+instance_num)
        print("等待无人机连接...")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print("无人机已连接！")
                break
        return drone

    async def arm_and_takeoff(self,instance_num,target_altitude=2.5):
        #连接无人机
        drone = System(port=55000+instance_num)
        await drone.connect(system_address=f"udp://:{60000+instance_num}")
        # print("等待无人机连接...")
        async for state in drone.core.connection_state():
            if state.is_connected:
                # print("无人机已连接！")
                break
        #解锁无人机
        # print("正在解锁无人机...")
        await drone.action.arm()
        # print("无人机已解锁！")
        #起飞
        # print(f"起飞至 {target_altitude} 米...")
        await drone.action.set_takeoff_altitude(target_altitude)
        await drone.action.takeoff()

        # 等待无人机达到目标高度
        async for position in drone.telemetry.position():
            altitude = position.relative_altitude_m
            if altitude >= target_altitude * 0.95:  # 允许一定的误差
                print(f"px4 {instance_num}已达到目标高度 {altitude:.2f} 米")
                break

    # async def run(self,instance_num):
    #     # drone = await self.connect(instance_num)
    #     await self.arm_and_takeoff(instance_num)

    async def run(self,instance_count): 
        # 创建一个包含 100 个 my_function 调用的列表，并传递参数
        tasks = [self.arm_and_takeoff(i) for i in range(instance_count)]
        
        # 使用 asyncio.gather 并发执行这些任务
        await asyncio.gather(*tasks)

    def takeoff(self,instance_num):
        asyncio.run(self.run(instance_num))




if __name__ == "__main__":
    

    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser()

    # 添加参数
    parser.add_argument("instance_count", type=int, help="实例个数", default=1)


    # 解析参数
    args = parser.parse_args()

    px4Control = PX4Control()
    px4Control.takeoff(args.instance_count)


