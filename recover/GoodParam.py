import subprocess
import asyncio
from mavsdk import System

async def change_param_px4(drone: System, param_name: str, new_param_value: float):
    await drone.param.set_param_float(param_name, new_param_value)
    print(f"已将参数 {param_name} 的值修改为: {new_param_value}")

async def run():
    # 启动PX4飞控程序
    drone = System()
    await drone.connect(system_address="udp://:60000")
    print("等待飞行器连接...")

    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"已连接到飞行器")
            break

    # 定义要修改的参数及其值
    params_to_change = {
        "MC_ROLL_P": 9.8,
        "MC_PITCH_P": 9.4,
        "MC_YAW_P": 0.1,
        "MC_YAW_WEIGHT": 0.1,
        "MPC_XY_P": 1.0,
        "MPC_Z_P": 0.6,
        "MC_PITCHRATE_P": 0.6,
        "MC_ROLLRATE_P": 0.02,
        "MC_YAWRATE_P": 0.01,      
        "MPC_TILTMAX_AIR": 89.0,    
        "MIS_YAW_ERR": 4.0,          
        "MPC_Z_VEL_MAX_DN": 3.0,
        "MPC_Z_VEL_MAX_UP": 1.7,      
        "MPC_TKO_SPEED": 4.8         
    }

    # 迭代修改参数
    for param_name, param_value in params_to_change.items():
        await change_param_px4(drone, param_name, param_value)
    

if __name__ == "__main__":
    asyncio.run(run())
