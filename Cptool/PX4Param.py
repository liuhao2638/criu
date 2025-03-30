from pymavlink import mavutil
import time
import json  # 导入json模块以读取文件
import multiprocessing
import argparse

# 读取配置文件
import yaml


    
class PX4Param:
    def __init__(self,instance_count,base_port,param_files):
        self.instance_count = instance_count
        self.base_port = base_port
        # 从文件中读取参数信息
        
        with open(param_files, 'r') as file:
            self.param_names = list(json.load(file).keys())
        # print(self.param_names)
        
    def change_single_params(self,instance_num,param_values):
        
        master = mavutil.mavlink_connection(f"udp:127.0.0.1:{self.base_port+instance_num}")
        master.wait_heartbeat()
        # print(instance_num)
        for param_name, param_value in zip(self.param_names,param_values):
            # 发送MAV_CMD_DO_SET_MODE命令来设置参数
            master.mav.param_set_send(
                master.target_system,
                master.target_component,
                param_name.encode('utf-8'),
                param_value,
                mavutil.mavlink.MAV_PARAM_TYPE_REAL32
            )
            # print(f"参数 {param_name} 修改为: {param_value}")
            # 等待一段时间以确保参数已设置
            time.sleep(0.1)

    def change_multiple_params(self, param_group):
        instances = (range(self.instance_count))

        args = zip(instances, param_group)
        # 并行执行计算得分函数
        with multiprocessing.Pool() as pool:
            pool.starmap(self.change_single_params, args)
            # pool.join()   # 等待所有任务完成

if __name__ == "__main__":
    with open("./Cptool/config.yaml", "r") as f:
        config = yaml.load(f.read(), Loader=yaml.FullLoader)
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser()

    # 添加参数
    parser.add_argument("--instance_count", type=int, help="实例个数", default=config["simulation"]["instance_count"])

    # 解析参数
    args = parser.parse_args()

   
    px4_param = PX4Param(args.instance_count,config["simulation"]["connect_port_1"],config["param_files"]["px4"])
    # px4_param.change_single_params(  0,  param_values = [
    #     9.8,       # MC_ROLL_P
    #     9.4,       # MC_PITCH_P
    #     0.1,       # MC_YAW_P
    #     0.1,       # MC_YAW_WEIGHT
    #     1.0,       # MPC_XY_P
    #     0.6,       # MPC_Z_P
    #     0.6,       # MC_PITCHRATE_P
    #     0.02,      # MC_ROLLRATE_P
    #     0.01,      # MC_YAWRATE_P
    #     89.0,      # MPC_TILTMAX_AIR
    #     4.0,       # MIS_YAW_ERR
    #     3.0,       # MPC_Z_VEL_MAX_DN
    #     1.7,       # MPC_Z_VEL_MAX_UP
    #     4.8        # MPC_TKO_SPEED
    # ])
    param_values = [9.8, 9.4, 0.1, 0.1, 1.0, 0.6, 0.6, 0.02, 0.01, 89.0, 4.0, 3.0, 1.7, 4.8]
    
    # param_group = [
    #     [9.8, 9.4, 0.1, 0.1, 1.0, 0.6, 0.6, 0.02, 0.01, 89.0, 4.0, 3.0, 1.7, 4.8],  # 实例 0 的 param_values
    #     [9.8, 9.4, 0.1, 0.1, 1.0, 0.6, 0.6, 0.02, 0.01, 89.0, 4.0, 3.0, 1.7, 4.8],  # 实例 1 的 param_values
    #     [9.8, 9.4, 0.1, 0.1, 1.0, 0.6, 0.6, 0.02, 0.01, 89.0, 4.0, 3.0, 1.7, 4.8],  # 实例 2 的 param_values
    #     [9.8, 9.4, 0.1, 0.1, 1.0, 0.6, 0.6, 0.02, 0.01, 89.0, 4.0, 3.0, 1.7, 4.8],  # 实例 3 的 param_values
    #     [9.8, 9.4, 0.1, 0.1, 1.0, 0.6, 0.6, 0.02, 0.01, 89.0, 4.0, 3.0, 1.7, 4.8]   # 实例 4 的 param_values
    # ]
    
    param_group =  [param_values]*args.instance_count
    
    print(param_group)
    px4_param.change_multiple_params(param_group)
