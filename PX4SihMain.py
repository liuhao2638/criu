import numpy as np
import time
import yaml
from PX4Mission import PX4Mission
from PX4Param import PX4Param
from PX4Score import PX4Score   
from PX4SihSim import PX4SihSim  

# 读取配置文件
with open("./Cptool/config.yaml", "r") as f:
    config = yaml.load(f.read(), Loader=yaml.FullLoader)

class PX4SihMain:
    def __init__(self):
        # 初始化类属性
        self.px4_working_dir=config['paths']['px4_working_dir']
        self.px4_build_dir=config['paths']['px4_build_dir']
        self.sim_speed=config["simulation"]["speed"]
        self.instance_count=config["simulation"]["instance_count"]
        self.is_daemon=config["simulation"]["daemon"]
        self.base_port = config["simulation"]["connect_port_2"]
        self.param_files = config["param_files"]["px4"]
        
    # def __init__(self, px4_working_dir, px4_build_dir, sim_speed, instance_count, is_daemon):
    #     # 初始化类属性
    #     self.px4_working_dir = px4_working_dir
    #     self.px4_build_dir = px4_build_dir
    #     self.sim_speed = sim_speed
    #     self.instance_count = instance_count
    #     self.is_daemon = is_daemon
        
    def TestParam(self,param_group):
        # 实例个数
        instance_count = len(param_group)
        
        # 启动多个实例的并行处理
        print(f"启动{instance_count}个实例...")
        px4SihSim = PX4SihSim(self.px4_working_dir,self.px4_build_dir,self.sim_speed,instance_count,self.is_daemon)
        # px4SihSim.start_sih_sitl()
        px4SihSim.start_sih_sitl_bash()
        time.sleep(15)
        print(f"完成...")
        
        
        
        print("开始设定执行任务...")
        px4Mission = PX4Mission(instance_count,self.base_port)
        px4Mission.start_multiple_mission()
        time.sleep(15)
        print(f"完成...")
        
        
        
        print("开始修改多个实例的参数...")
        px4_param = PX4Param(instance_count,self.base_port,self.param_files)
        px4_param.change_multiple_params(param_group)
        time.sleep(5)
        print(f"完成...")
        
        
        
        print("开始计算多个实例的得分...")
        px4Score = PX4Score(instance_count, self.sim_speed, self.base_port)
        scores = px4Score.count_score()
        print(f"完成...")
        
        # 回收所有px4子进程
        print("回收所有px4子进程...")
        px4SihSim.stop_sih_sitl()
        # MISSION
        # param
        # score
        return scores
        
        
if __name__ == "__main__":
    instance_count = 500
    param_values = [9.8, 9.4, 0.1, 0.1, 1.0, 0.6, 0.6, 0.02, 0.01, 89.0, 4.0, 3.0, 1.7, 4.8]
    param_group =  [param_values]*instance_count
    
    start_time = time.perf_counter()
    # 启动多个实例的并行处理
    px4SihMain = PX4SihMain()
    scores = px4SihMain.TestParam(param_group)
    
    print(scores)
    nan_indices = np.where(np.isnan(scores))[0]
    print("以下编号测试失败:", nan_indices)
    
    end_time = time.perf_counter()
    print(f"测试{instance_count}个参数 耗时: {end_time - start_time:.4f} 秒")
    