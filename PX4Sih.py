import time
import argparse
import os
import subprocess
import multiprocessing
# from concurrent.futures import ThreadPoolExecutor
import yaml

# 读取配置文件
with open("./Cptool/config.yaml", "r") as f:
    config = yaml.load(f.read(), Loader=yaml.FullLoader)


class PX4Sih:

    def __init__(self, px4_working_dir, px4_build_dir, sim_speed, instance_count, is_daemon):
        # 初始化类属性
        self.px4_working_dir = px4_working_dir
        self.px4_build_dir = px4_build_dir
        self.sim_speed = sim_speed
        self.instance_count = instance_count
        self.is_daemon = is_daemon
        # 初始化用于存储模拟实例进程的列表
        self.processes = []

    # 开启一个硬件内仿真(sih)进程，返回进程PID
    def start_single_sih_sitl(self, instance_num):
        # 设定px4进程的工作目录
        # px4_working_dir = f"{self.px4_working_dir}/instance_{instance_num}"
        px4_working_dir = f"{self.px4_working_dir}/instance/instance_{instance_num}"
        # os.system(f"rm -rf {px4_working_dir} && mkdir -p {px4_working_dir}")
        os.system(f"mkdir -p {px4_working_dir}")


        px4_env = os.environ.copy()
        px4_env["PX4_SIMULATOR"] = "sihsim"
        px4_env["PX4_SYS_AUTOSTART"] = "10040"
        px4_env["PX4_SIM_SPEED_FACTOR"] = f"{self.sim_speed}"

        if self.is_daemon == "True":
            # 开启一个硬件内仿真(sih)进程，开启shell
            # px4 sih仿真启动命令
            start_px4_sih_sitl_command = [
                f"{self.px4_build_dir}/bin/px4",
                "-i",
                f"{instance_num}",
                "-d",
                f"{self.px4_build_dir}/etc",
                "-w",
                f"{px4_working_dir}",
                "-s",
                f"{self.px4_build_dir}/etc/init.d-posix/rcS",
            ]
            # 打开文件来重定向输出
            # stdout_file = open(f"{px4_working_dir}/out.log", "w")
            stdout_file = open(f"{self.px4_working_dir}/log/{instance_num}.log", "w")

            process = subprocess.Popen(
                start_px4_sih_sitl_command, env=px4_env, stdout=stdout_file, stderr=stdout_file  # 重定向stdout到文件  # 重定向stderr到文件
            )
        elif self.is_daemon == "False":
            # px4 sih仿真启动命令
            start_px4_sih_sitl_command = [
                f"{self.px4_build_dir}/bin/px4",
                "-i",
                f"{instance_num}",
                f"{self.px4_build_dir}/etc",
                "-w",
                f"{px4_working_dir}",
                "-s",
                f"{self.px4_build_dir}/etc/init.d-posix/rcS",
            ]
            process = subprocess.Popen(
                start_px4_sih_sitl_command, env=px4_env
            )
            # print(f"instance_count:{instance_count} Process ID (PID):{process.pid}")
        return process

    # 并行执行多个Sih实例的启动
    def start_sih_sitl(self):
        instance_count = self.instance_count
        
        # 清理并准备工作目录
        os.system(f"rm -rf {self.px4_working_dir}")
        os.system(f"mkdir -p {self.px4_working_dir}/instance")
        os.system(f"mkdir -p {self.px4_working_dir}/log")
        # 清理所有系统中的 px4 进程
        os.system("killall px4")


        # 使用 Process 来并行执行进程
        for i in range(instance_count):  # 启动 instance_count 个实例
            p = multiprocessing.Process(target=self.start_single_sih_sitl, args=(i,))
            self.processes.append(p)
            p.start()

        # 等待所有进程完成
        for p in self.processes:
            p.join()
        print(f"px4实例数量：{instance_count}")
        print("All Sih PX4 instances started.")
        # return self.processes

    # 回收所有px4子进程
    def stop_sih_sitl(self):
        for p in self.processes:
            p.terminate()
            # 等待子进程真正结束
            p.join()

    #执行起飞前检查

if __name__ == "__main__":
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser()

    # 添加参数
    parser.add_argument("--instance_count", type=int, help="实例个数", default=config["simulation"]["instance_count"])
    parser.add_argument("--sim_speed", type=int, help="sih仿真速度", default=config["simulation"]["speed"])
    parser.add_argument("--is_daemon", type=str, help="是否开启交互", default=config["simulation"]["daemon"])
    # 解析参数
    args = parser.parse_args()

    # print(args.instance_count)
    # print(args.sim_speed)
    # print(args.is_daemon)

    # 启动多个实例的并行处理
    px4Sih = PX4Sih(
        px4_working_dir=config['paths']['px4_working_dir'],
        px4_build_dir=config['paths']['px4_build_dir'],
        sim_speed=args.sim_speed,
        instance_count=args.instance_count,
        is_daemon=args.is_daemon
    )
    # px4Sih.start_sih_sitl()
    px4Sih.start_sih_sitl()

    try:
        print("运行中，按 Ctrl+C 退出")
        while True:
            # 阻塞程序，保持运行
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n检测到 Ctrl+C，清理px4实例...")
        px4Sih.stop_sih_sitl()
        print("程序已退出")
