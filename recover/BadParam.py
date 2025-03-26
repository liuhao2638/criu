import subprocess
import asyncio
from mavsdk import System


async def change_param_px4(drone: System, param_name: str, new_param_value: float):
    await drone.param.set_param_float(param_name, new_param_value)


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
    original_params = {
        "MC_ROLL_P": 6.5,
        "MC_PITCH_P": 6.5,
        "MC_YAW_P": 2.8,
        "MC_YAW_WEIGHT": 0.4,
        "MPC_XY_P": 0.9,
        "MPC_Z_P": 1.0,
        "MC_PITCHRATE_P": 0.15,
        "MC_ROLLRATE_P": 0.15,
        "MC_YAWRATE_P": 0.2,
        "MPC_TILTMAX_AIR": 45.0,
        "MIS_YAW_ERR": 12.0,
        "MPC_Z_VEL_MAX_DN": 1.0,
        "MPC_Z_VEL_MAX_UP": 3.0,
        "MPC_TKO_SPEED": 1.5,
    }

    print("\n恢复参数到原始值...")
    for param_name, original_value in original_params.items():
        await change_param_px4(drone, param_name, original_value)
        print(f"参数 {param_name} 已恢复为默认值: {original_value}")


if __name__ == "__main__":
    asyncio.run(run())
