from pymavlink import mavutil
import time
import math


import multiprocessing
import argparse

# 读取配置文件
import yaml

with open("./Cptool/config.yaml", "r") as f:
    config = yaml.load(f.read(), Loader=yaml.FullLoader)



class PX4Score:
    def __init__(self, instance_count, sim_speed,base_port):
        self.instance_count = instance_count
        self.sim_speed = sim_speed
        self.base_port = base_port
    # 计算所有px4实例的适应度得分
    def count_score(self):
        instances = list(range(self.instance_count))
        scores = list(range(self.instance_count))

        # 并行执行计算得分函数
        with multiprocessing.Pool() as pool:
            scores = pool.map(self.count_single_score, instances)

        print(scores)

        return scores
    # 计算单个px4实例的适应度得分
    def count_single_score(self, instance):
        master = mavutil.mavlink_connection(f"udp:127.0.0.1:{self.base_port + instance}")
        return self.monitor_px4_state(master)

    # 从 LOCAL_POSITION_NED 和 ATTITUDE 消息中提取当前状态。
    # :param pos_msg: LOCAL_POSITION_NED 消息
    # :param att_msg: ATTITUDE 消息
    # :return: 返回当前状态的字典
    def get_current_state(self, pos_msg, att_msg):

        return {
            "position": {"x": pos_msg.x, "y": pos_msg.y, "z": pos_msg.z},
            "velocity": {"vx": pos_msg.vx, "vy": pos_msg.vy, "vz": pos_msg.vz},
            "attitude": {"roll": att_msg.roll, "pitch": att_msg.pitch, "yaw": att_msg.yaw},
            "angular_velocity": {"rollspeed": att_msg.rollspeed, "pitchspeed": att_msg.pitchspeed, "yawspeed": att_msg.yawspeed},
        }

    # 从 POSITION_TARGET_LOCAL_NED 和 ATTITUDE_TARGET 消息中提取设定值。
    # :param pos_target_msg: POSITION_TARGET_LOCAL_NED 消息
    # :param att_target_msg: ATTITUDE_TARGET 消息
    # :return: 返回设定值的字典
    # def get_setpoints(self, pos_target_msg, att_target_msg):

    #     return {
    #         "position_setpoint": {"x": pos_target_msg.x, "y": pos_target_msg.y, "z": pos_target_msg.z},
    #         "velocity_setpoint": {"vx": pos_target_msg.vx, "vy": pos_target_msg.vy, "vz": pos_target_msg.vz},
    #         "attitude_setpoint": {
    #             "roll": att_target_msg.body_roll_rate,
    #             "pitch": att_target_msg.body_pitch_rate,
    #             "yaw": pos_target_msg.yaw,
    #         },
    #         "angular_velocity_setpoint": {
    #             "rollspeed": att_target_msg.body_roll_rate,
    #             "pitchspeed": att_target_msg.body_pitch_rate,
    #             "yawspeed": att_target_msg.body_pitch_rate,
    #         },
    #     }
    def get_setpoints(self,pos_target_msg, att_target_msg):
        """
        从 POSITION_TARGET_LOCAL_NED 和 ATTITUDE_TARGET 消息中提取设定值。

        :param pos_target_msg: POSITION_TARGET_LOCAL_NED 消息
        :param att_target_msg: ATTITUDE_TARGET 消息
        :return: 返回设定值的字典
        """
        # 从 ATTITUDE_TARGET 消息中提取四元数
        q_w = att_target_msg.q[0]
        q_x = att_target_msg.q[1]
        q_y = att_target_msg.q[2]
        q_z = att_target_msg.q[3]

        # 将四元数转换为欧拉角（roll, pitch, yaw）
        # Roll (x-axis rotation)
        roll = math.atan2(2 * (q_w * q_x + q_y * q_z), 1 - 2 * (q_x**2 + q_y**2))
        # Pitch (y-axis rotation)
        pitch = math.asin(2 * (q_w * q_y - q_z * q_x))

        return {
            "position_setpoint": {"x": pos_target_msg.x, "y": pos_target_msg.y, "z": pos_target_msg.z},
            "velocity_setpoint": {"vx": pos_target_msg.vx, "vy": pos_target_msg.vy, "vz": pos_target_msg.vz},
            "attitude_setpoint": {
                "roll": roll,  # 计算出的 roll 角
                "pitch": pitch,  # 计算出的 pitch 角
                "yaw": pos_target_msg.yaw,  # 使用 POSITION_TARGET_LOCAL_NED 中的 yaw
            },
            "angular_velocity_setpoint": {
                "rollspeed": att_target_msg.body_roll_rate,
                "pitchspeed": att_target_msg.body_pitch_rate,
                "yawspeed": att_target_msg.body_yaw_rate,  # 修正为 body_yaw_rate
            },
        }


    # 计算当前状态与设定值之间的差值。
    # :param current_state: 当前状态
    # :param setpoint: 设定值
    # :return: 返回差值的字典
    def calculate_difference(self, current_state, setpoint):

        return {
            "position": {
                "x": abs(current_state["position"]["x"] - setpoint["position_setpoint"]["x"]),
                "y": abs(current_state["position"]["y"] - setpoint["position_setpoint"]["y"]),
                "z": abs(current_state["position"]["z"] - setpoint["position_setpoint"]["z"]),
            },
            "velocity": {
                "vx": abs(current_state["velocity"]["vx"] - setpoint["velocity_setpoint"]["vx"]),
                "vy": abs(current_state["velocity"]["vy"] - setpoint["velocity_setpoint"]["vy"]),
                "vz": abs(current_state["velocity"]["vz"] - setpoint["velocity_setpoint"]["vz"]),
            },
            "attitude": {
                "roll": abs(current_state["attitude"]["roll"] - setpoint["attitude_setpoint"]["roll"]),
                "pitch": abs(current_state["attitude"]["pitch"] - setpoint["attitude_setpoint"]["pitch"]),
                "yaw": abs(current_state["attitude"]["yaw"] - setpoint["attitude_setpoint"]["yaw"]),
            },
            "angular_velocity": {
                "rollspeed": abs(current_state["angular_velocity"]["rollspeed"] - setpoint["angular_velocity_setpoint"]["rollspeed"]),
                "pitchspeed": abs(current_state["angular_velocity"]["pitchspeed"] - setpoint["angular_velocity_setpoint"]["pitchspeed"]),
                "yawspeed": abs(current_state["angular_velocity"]["yawspeed"] - setpoint["angular_velocity_setpoint"]["yawspeed"]),
            },
        }

    # 将单个维度的差值归一化到0-100分。
    # :param value: 当前维度的差值
    # :param min_value: 差值的最小值
    # :param max_value: 差值的最大值
    # :return: 归一化后的分数（0-100）
    def normalize_score(self, value, min_value, max_value):
        if value < min_value:
            return 0
        # elif value > max_value:
        #     return 100
        else:
            return 100 * (value - min_value) / (max_value - min_value)

    # 计算12维度差值的总分。
    # :param difference: 包含12维度差值的字典
    # :param min_values: 每个维度差值的最小值
    # :param max_values: 每个维度差值的最大值
    # :param weights: 每个维度的权重
    # :return: 总分（0-100）
    def calculate_total_score(self, difference, min_values, max_values, weights):

        total_weight = sum(weights[key][subkey] for key in weights for subkey in weights[key])
        total_score = 0

        # 遍历每个维度，计算归一化分数并加权求和
        for key in difference:
            for subkey in difference[key]:
                value = abs(difference[key][subkey])  # 取绝对值
                score = self.normalize_score(value, min_values[key][subkey], max_values[key][subkey])
                total_score += score * weights[key][subkey]

        return total_score / total_weight  # 归一化到 0-100 之间

    # 监听PX4消息流，计算每一秒内差值的平均值，并输出分数。
    def monitor_px4_state(self, master):

        # 初始化差值累加器
        total_difference = {
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "velocity": {"vx": 0.0, "vy": 0.0, "vz": 0.0},
            "attitude": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0},
            "angular_velocity": {"rollspeed": 0.0, "pitchspeed": 0.0, "yawspeed": 0.0},
        }

        # 初始化计数器
        count = 0

        # 开始时间
        start_time = time.time()

        # 定义每个维度差值的范围和权重
        min_values = {
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "velocity": {"vx": 0.0, "vy": 0.0, "vz": 0.0},
            "attitude": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0},
            "angular_velocity": {"rollspeed": 0.0, "pitchspeed": 0.0, "yawspeed": 0.0},
        }

        max_values = {
            "position": {"x": 9.18, "y": 9.18, "z": 3.49},
            "velocity": {"vx": 4.62, "vy": 4.62, "vz": 4.21},
            "attitude": {
                "roll": 2.03 * (math.pi / 180),  # 度 -> 弧度
                "pitch": 4.31 * (math.pi / 180),  # 度 -> 弧度
                "yaw": 6.23 * (math.pi / 180),  # 度 -> 弧度
            },
            "angular_velocity": {
                "rollspeed": 3.65 * (math.pi / 180),  # 度/秒 -> 弧度/秒
                "pitchspeed": 15.41 * (math.pi / 180),  # 度/秒 -> 弧度/秒
                "yawspeed": 14.32 * (math.pi / 180),  # 度/秒 -> 弧度/秒
            },
            # "attitude": {"roll": 2.03, "pitch": 4.31, "yaw": 6.23},
            # "angular_velocity": {"rollspeed": 3.65, "pitchspeed": 15.41, "yawspeed": 14.32},
        }
        # max_values = {
        #     "position": {"x": 9.18, "y": 9.18, "z": 3.49},
        #     "velocity": {"vx": 4.62, "vy": 4.62, "vz": 4.21},
        #     "attitude": {
        #         "roll": 2.03 ,  # 度 -> 弧度
        #         "pitch": 4.31,  # 度 -> 弧度
        #         "yaw": 6.23 ,  # 度 -> 弧度
        #     },
        #     "angular_velocity": {
        #         "rollspeed": 3.65,  # 度/秒 -> 弧度/秒
        #         "pitchspeed": 15.41,  # 度/秒 -> 弧度/秒
        #         "yawspeed": 14.32,  # 度/秒 -> 弧度/秒
        #     },
        #     # "attitude": {"roll": 2.03, "pitch": 4.31, "yaw": 6.23},
        #     # "angular_velocity": {"rollspeed": 3.65, "pitchspeed": 15.41, "yawspeed": 14.32},
        # }

        weights = {
            "position": {"x": 1.0, "y": 1.0, "z": 1.0},
            "velocity": {"vx": 1.0, "vy": 1.0, "vz": 1.0},
            "attitude": {"roll": 1.0, "pitch": 1.0, "yaw": 1.0},
            "angular_velocity": {"rollspeed": 1.0, "pitchspeed": 1.0, "yawspeed": 1.0},
        }
        while True:
            # 监听消息流
            # msg = master.recv_match(blocking=True)

            # if msg is not None:
            #     # 获取当前状态和设定值
            #     if msg.get_type() == "LOCAL_POSITION_NED":
            #         pos_msg = msg
            #     elif msg.get_type() == "ATTITUDE":
            #         att_msg = msg
            #     elif msg.get_type() == "POSITION_TARGET_LOCAL_NED":
            #         pos_target_msg = msg
            #     elif msg.get_type() == "ATTITUDE_TARGET":
            #         att_target_msg = msg

            # 获取 ATTITUDE 消息（姿态和角速度）
            att_msg = master.recv_match(type="ATTITUDE", blocking=True, timeout=1)
            # 获取 ATTITUDE_TARGET 消息（姿态和角速度设定值）
            att_target_msg = master.recv_match(type="ATTITUDE_TARGET", blocking=True, timeout=1)
            # 获取 POSITION_TARGET_LOCAL_NED 消息（位置和速度设定值）
            pos_target_msg = master.recv_match(type="POSITION_TARGET_LOCAL_NED", blocking=True, timeout=1)
            # 获取 LOCAL_POSITION_NED 消息（位置和速度）
            pos_msg = master.recv_match(type="LOCAL_POSITION_NED", blocking=True, timeout=1)

            #print(f"att_msg: {att_msg.time_boot_ms}")
            #print(f"att_target_msg: {att_target_msg.time_boot_ms}")
            #print(f"pos_target_msg: {pos_target_msg.time_boot_ms}")
            #print(f"pos_msg: {pos_msg.time_boot_ms}")


            # 当所有消息都收到后，计算差值
            # if all(var in locals() for var in ["pos_msg", "att_msg", "pos_target_msg", "att_target_msg"]):
            # 获取当前状态和设定值
            current_state = self.get_current_state(pos_msg, att_msg)
            setpoint = self.get_setpoints(pos_target_msg, att_target_msg)

            # 计算差值
            difference = self.calculate_difference(current_state, setpoint)
            # print(f'current_state: {current_state}')
            # print(f'setpoint: {setpoint}')
            # print(f'difference: {current_state}')
            # print(f'att_msg: {att_msg}')
            # print(f'att_target_msg: {att_target_msg}')

            # 累加差值
            for key in total_difference:
                for subkey in total_difference[key]:
                    total_difference[key][subkey] += difference[key][subkey]

            # 增加计数器
            count += 1

            # 如果达到1秒，计算平均值并输出
            if time.time() - start_time >= 1.0:
                if count > 0:
                    # 计算平均值
                    average_difference = {
                        "position": {
                            "x": total_difference["position"]["x"] / count,
                            "y": total_difference["position"]["y"] / count,
                            "z": total_difference["position"]["z"] / count,
                        },
                        "velocity": {
                            "vx": total_difference["velocity"]["vx"] / count,
                            "vy": total_difference["velocity"]["vy"] / count,
                            "vz": total_difference["velocity"]["vz"] / count,
                        },
                        "attitude": {
                            "roll": total_difference["attitude"]["roll"] / count,
                            "pitch": total_difference["attitude"]["pitch"] / count,
                            "yaw": total_difference["attitude"]["yaw"] / count,
                        },
                        "angular_velocity": {
                            "rollspeed": total_difference["angular_velocity"]["rollspeed"] / count,
                            "pitchspeed": total_difference["angular_velocity"]["pitchspeed"] / count,
                            "yawspeed": total_difference["angular_velocity"]["yawspeed"] / count,
                        },
                    }

                    # 计算总分
                    total_score = self.calculate_total_score(average_difference, min_values, max_values, weights)

                    # 输出平均值和总分
                    # print("1秒内差值的平均值:")
                    # for key in average_difference:
                    #     print(f"{key}: {average_difference[key]}")
                    # print(f"总分: {total_score:.2f}")

                # 重置累加器和计数器
                total_difference = {
                    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "velocity": {"vx": 0.0, "vy": 0.0, "vz": 0.0},
                    "attitude": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0},
                    "angular_velocity": {"rollspeed": 0.0, "pitchspeed": 0.0, "yawspeed": 0.0},
                }
                count = 0
                start_time = time.time()
                # print(total_score)
                break
        return total_score


if __name__ == "__main__":
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser()

    # 添加参数
    parser.add_argument("instance_count", type=int, help="实例个数", default=1)
    parser.add_argument("sim_speed", type=int, help="sih仿真速度", default=config["simulation"]["speed"])

    # 解析参数
    args = parser.parse_args()

    px4Score = PX4Score(args.instance_count, args.sim_speed,config["simulation"]["connect_port"])
    px4Score.count_score()
    # px4Score.monitor_px4_state(60000)
