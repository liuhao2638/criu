import argparse

import os

# 读取配置文件
import yaml

with open("./Cptool/config.yaml", "r") as f:
    config = yaml.load(f.read(), Loader=yaml.FullLoader)


class SihDisplay:

    def __init__(self):
        self.sim_speed = config["simulation"]["speed"]
        pass

    # 开启一个可视化
    def start_display(self, instance_num):
        # print(px4_working_dir)
        jmavsim_dir = config["paths"]["jmavsim_dir"]
        display_port = config["simulation"]["display_port"]

        # ./Tools/simulation/jmavsim/jmavsim_run.sh -p 19410 -u -q -o
        os.system(f"{jmavsim_dir}/jmavsim_run.sh -p {display_port+instance_num} -u -q -o")


# 单例
sihDisplay = SihDisplay()


if __name__ == "__main__":
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser()

    # 添加参数
    parser.add_argument("instance_num", type=int, help="实例编号", default=0)

    # 解析参数
    args = parser.parse_args()

    # 启动多个实例的并行处理
    sihDisplay.start_display(args.instance_num)
