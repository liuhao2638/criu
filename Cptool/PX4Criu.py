import argparse
import time
import os
import subprocess
import multiprocessing
import psutil
import yaml
import re

import pickle


from PX4Mission import PX4Mission
from PX4Param import PX4Param
from PX4SihSim import PX4SihSim  


class PX4Criu:
    def __init__(self):
        with open("./config.yaml", "r") as f:
            config = yaml.load(f.read(), Loader=yaml.FullLoader)
        # 初始化类属性
        self.root_dir=config['paths']['root_dir']
        self.px4_working_dir=config['paths']['px4_working_dir']
        self.criu_imgs_dir=config['paths']['criu_imgs_dir']
        self.px4_build_dir=config['paths']['px4_build_dir']
        self.sim_speed=config["simulation"]["speed"]
        self.instance_count=config["simulation"]["instance_count"]
        self.is_daemon=config["simulation"]["daemon"]
        self.base_port = config["simulation"]["connect_port_2"]
        self.param_files = config["param_files"]["px4"]
        #初始化px4工具类
        self.px4SihSim = PX4SihSim(self.px4_working_dir,self.px4_build_dir,self.sim_speed,self.instance_count,self.is_daemon)
        self.px4Mission = PX4Mission(self.instance_count,self.base_port)

        # 初始化用于存储模拟实例进程的列表
        self.processes = []

    def find_px4_sih_pid(self):
        # 存储 PID 和实例号的字典
        pid_dict = {}

        cmd = "ps -aux | grep 'px4_sitl_default/bin/px4'"
        output = subprocess.check_output(cmd, shell=True, text=True)
        # print(output)

        # 将输出按行分割
        lines = output.strip().split('\n')
        if not lines:
            print("未找到px4进程")
            return None
        
        # 处理每一行
        for line in lines:
            # 提取 PID (第2个字段)
            fields = line.split()
            pid = int(fields[1])
            
            # 使用正则表达式提取实例号
            instance_match = re.search(r'-i\s+(\d+)', line)
            if instance_match:
                instance_num = int(instance_match.group(1))
                pid_dict[instance_num] = pid
        # 按实例号排序并创建 PID 数组
        pids = [0] * (max(pid_dict.keys(), default=-1) + 1)
        for instance_num, pid in pid_dict.items():
            pids[instance_num] = pid
            
        return pids
    
    def dump_single_px4_proecss(self,instance_num,pid):
        img_dir = f"{self.px4_working_dir}/criu_img_dir/px4_{instance_num}_img"
        os.system(f"rm -rf {img_dir}")
        os.system(f"mkdir -p {img_dir}")
        # os.system(f"sudo criu dump -D {img_dir} -j --tcp-established --file-locks -t {pid}")
        cmd = ["sudo","criu","dump","-D",img_dir,"-j","--tcp-established","--file-locks","-t",f"{pid}"]
        subprocess.Popen(cmd)
        # return process.pid


    def dump_multiple_px4_proecss(self,instances,pids):
        args = zip(instances,pids)
        with multiprocessing.Pool() as pool:
            pool.starmap(self.dump_single_px4_proecss, args)

    def restore_single_px4_proecss(self,instance_num):
        img_dir = f"{self.px4_working_dir}/criu_img_dir/px4_{instance_num}_img"
        # os.system(f"sudo criu restore -D {img_dir} -j --tcp-established")
        cmd = ["sudo","criu","restore","-D",img_dir,"-j","--tcp-established"]
        subprocess.Popen(cmd)
        # return process.pid  

    def restore_multiple_px4_proecss(self,instances):
        # 使用 Process 来并行执行进程
        with multiprocessing.Pool() as pool:
            pool.map(self.restore_single_px4_proecss, instances)
        time.sleep(5)
        pids = px4Criu.find_px4_sih_pid()
        print(pids)
        return pids



    def recover_criu_imgs(self):
        os.system(f"rm -rf {self.px4_working_dir}/")
        os.system(f"cp -r {self.criu_imgs_dir}/ {self.px4_working_dir}/")
        time.sleep(1)
        print("已恢复criu imgs和px4工作目录")


    def save_criu_imgs(self):
        os.system(f"rm -rf {self.criu_imgs_dir}")
        os.system(f"cp -r {self.px4_working_dir}/ {self.criu_imgs_dir}")
        time.sleep(1)
        print("已保存criu imgs和px4工作目录")

        

    #创建instance_count个sih检查点
    def make_single_px4_sih_checkpoint(self,instance_num):
        
        pid = self.px4SihSim.start_single_sih_sitl(instance_num)
        print(f"开启仿真{instance_num}")
        time.sleep(5)
        self.px4Mission.start_single_mission(instance_num)
        time.sleep(15)

        self.dump_single_px4_proecss(instance_num,pid)
        print(f"成功保存px4实例{instance_num}")
        # return pid

    def make_multiple_px4_sih_checkpoint(self,instance_count):
        os.system(f"rm -rf {self.px4_working_dir}/")
        os.system(f"rm -rf {self.criu_imgs_dir}")
        os.system("killall px4")
        
        # with multiprocessing.Pool() as pool:
        #     pool.map(self.make_single_px4_sih_checkpoint, range(instance_count))
        # time.sleep(10)
        for i in range(instance_count):
            self.make_single_px4_sih_checkpoint(i)
        
        



if __name__ == "__main__":
    px4Criu = PX4Criu()
    px4Criu.make_multiple_px4_sih_checkpoint(100)
    px4Criu.save_criu_imgs()


    print("开始恢复")
    pids = px4Criu.restore_multiple_px4_proecss(list(range(100)))
    
    time.sleep(10)
    print("开始回溯")
    px4Criu.dump_multiple_px4_proecss(list(range(100)),list(pids))
    time.sleep(1)

    px4Criu.recover_criu_imgs()

    # while True:
    #     print("开始恢复")
    #     pids = px4Criu.restore_multiple_px4_proecss(list(range(100)))
        
    #     time.sleep(10)
    #     print("开始回溯")
    #     px4Criu.dump_multiple_px4_proecss(list(range(100)),list(pids))
    #     time.sleep(1)

    #     px4Criu.recover_criu_imgs()

 
