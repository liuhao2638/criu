from pymavlink import mavutil
import time
import math
import multiprocessing
import argparse
import yaml


# 读取配置文件
with open("./Cptool/config.yaml", "r") as f:
    config = yaml.load(f.read(), Loader=yaml.FullLoader)


class PX4Score:
    def __init__(self, instance_count, sim_speed, base_port):
        """
        初始化PX4Score类。

        :param instance_count: PX4实例的数量
        :param sim_speed: 仿真速度
        :param base_port: 基础端口号
        """
        self.instance_count = instance_count
        self.sim_speed = sim_speed
        self.base_port = base_port
        # self.masters = [
        #     mavutil.mavlink_connection(f"udp:127.0.0.1:{self.base_port + instance}")
        #     for instance in range(instance_count)
        # ]

    def count_score(self):
        """
        计算所有PX4实例的适应度得分。

        :return: 返回所有实例的得分列表
        """
        instances = list(range(self.instance_count))
        scores = list(range(self.instance_count))

        # 并行执行计算得分函数
        with multiprocessing.Pool() as pool:
            scores = pool.map(self._count_single_score, instances)
            # pool.join()   # 等待所有任务完成

        # print(scores)
        
        return scores

    def _count_single_score(self, instance):
        """
        计算单个PX4实例的适应度得分。

        :param instance: PX4实例的编号
        :return: 返回该实例的得分
        """
        master = mavutil.mavlink_connection(f"udp:127.0.0.1:{self.base_port + instance}")
        return self._monitor_px4_state(master)

    def _get_current_state(self, pos_msg, att_msg):
        """
        从 LOCAL_POSITION_NED 和 ATTITUDE 消息中提取当前状态。

        :param pos_msg: LOCAL_POSITION_NED 消息
        :param att_msg: ATTITUDE 消息
        :return: 返回当前状态的字典
        """
        return {
            "position": {"x": pos_msg.x, "y": pos_msg.y, "z": pos_msg.z},
            "velocity": {"vx": pos_msg.vx, "vy": pos_msg.vy, "vz": pos_msg.vz},
            "attitude": {"roll": att_msg.roll, "pitch": att_msg.pitch, "yaw": att_msg.yaw},
            "angular_velocity": {"rollspeed": att_msg.rollspeed, "pitchspeed": att_msg.pitchspeed, "yawspeed": att_msg.yawspeed},
        }

    def _get_setpoints(self, pos_target_msg, att_target_msg):
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
        roll = math.atan2(2 * (q_w * q_x + q_y * q_z), 1 - 2 * (q_x**2 + q_y**2))
        pitch = math.asin(2 * (q_w * q_y - q_z * q_x))

        return {
            "position_setpoint": {"x": pos_target_msg.x, "y": pos_target_msg.y, "z": pos_target_msg.z},
            "velocity_setpoint": {"vx": pos_target_msg.vx, "vy": pos_target_msg.vy, "vz": pos_target_msg.vz},
            "attitude_setpoint": {
                "roll": roll,
                "pitch": pitch,
                "yaw": pos_target_msg.yaw,
            },
            "angular_velocity_setpoint": {
                "rollspeed": att_target_msg.body_roll_rate,
                "pitchspeed": att_target_msg.body_pitch_rate,
                "yawspeed": att_target_msg.body_yaw_rate,
            },
        }

    def _calculate_difference(self, current_state, setpoint):
        """
        计算当前状态与设定值之间的差值。

        :param current_state: 当前状态
        :param setpoint: 设定值
        :return: 返回差值的字典
        """
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

    def _normalize_score(self, value, min_value, max_value):
        """
        将单个维度的差值归一化到0-100分。

        :param value: 当前维度的差值
        :param min_value: 差值的最小值
        :param max_value: 差值的最大值
        :return: 归一化后的分数（0-100）
        """
        if value < min_value:
            return 0
        else:
            return 100 * (value - min_value) / (max_value - min_value)

    def _calculate_total_score(self, difference, min_values, max_values, weights):
        """
        计算12维度差值的总分。

        :param difference: 包含12维度差值的字典
        :param min_values: 每个维度差值的最小值
        :param max_values: 每个维度差值的最大值
        :param weights: 每个维度的权重
        :return: 总分（0-100）
        """
        total_weight = sum(weights[key][subkey] for key in weights for subkey in weights[key])
        total_score = 0

        # 遍历每个维度，计算归一化分数并加权求和
        for key in difference:
            for subkey in difference[key]:
                value = abs(difference[key][subkey])
                score = self._normalize_score(value, min_values[key][subkey], max_values[key][subkey])
                total_score += score * weights[key][subkey]

        return total_score / total_weight

    def _monitor_px4_state(self, master):
        """
        监听PX4消息流，计算每一秒内差值的平均值，并输出分数。

        :param master: MAVLink连接对象
        :return: 返回总分
        """
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
                "roll": 2.03 * (math.pi / 180),
                "pitch": 4.31 * (math.pi / 180),
                "yaw": 6.23 * (math.pi / 180),
            },
            "angular_velocity": {
                "rollspeed": 3.65 * (math.pi / 180),
                "pitchspeed": 15.41 * (math.pi / 180),
                "yawspeed": 14.32 * (math.pi / 180),
            },
        }

        weights = {
            "position": {"x": 1.0, "y": 1.0, "z": 1.0},
            "velocity": {"vx": 1.0, "vy": 1.0, "vz": 1.0},
            "attitude": {"roll": 1.0, "pitch": 1.0, "yaw": 1.0},
            "angular_velocity": {"rollspeed": 1.0, "pitchspeed": 1.0, "yawspeed": 1.0},
        }

        while True:
            # 获取消息
            msg_timeout = 0.5
            att_msg = master.recv_match(type="ATTITUDE", blocking=True, timeout=msg_timeout)
            att_target_msg = master.recv_match(type="ATTITUDE_TARGET", blocking=True, timeout=msg_timeout)
            pos_target_msg = master.recv_match(type="POSITION_TARGET_LOCAL_NED", blocking=True, timeout=msg_timeout)
            pos_msg = master.recv_match(type="LOCAL_POSITION_NED", blocking=True, timeout=msg_timeout)
            
            if any(msg is None for msg in [att_msg, att_target_msg, pos_target_msg, pos_msg]):
                # print("接收到无效的消息，程序终止")
                return 0 # 如果你想终止程序，可以使用return

            
            # 计算当前状态和设定值
            current_state = self._get_current_state(pos_msg, att_msg)
            setpoint = self._get_setpoints(pos_target_msg, att_target_msg)

            # 计算差值
            difference = self._calculate_difference(current_state, setpoint)

            # 累加差值
            for key in total_difference:
                for subkey in total_difference[key]:
                    total_difference[key][subkey] += difference[key][subkey]

            # 增加计数器
            count += 1

            # 如果达到1秒，计算平均值并输出
            if time.time() - start_time >= 1.0/self.sim_speed:
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
                    total_score = self._calculate_total_score(average_difference, min_values, max_values, weights)

                # 重置累加器和计数器
                total_difference = {
                    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "velocity": {"vx": 0.0, "vy": 0.0, "vz": 0.0},
                    "attitude": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0},
                    "angular_velocity": {"rollspeed": 0.0, "pitchspeed": 0.0, "yawspeed": 0.0},
                }
                count = 0
                start_time = time.time()
                break

        return total_score


if __name__ == "__main__":
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser()

    # 添加参数
    parser.add_argument("--instance_count", type=int, help="实例个数", default=config["simulation"]["instance_count"])
    parser.add_argument("--sim_speed", type=int, help="sih仿真速度", default=config["simulation"]["speed"])

    # 解析参数
    args = parser.parse_args()

    px4Score = PX4Score(args.instance_count, args.sim_speed, config["simulation"]["connect_port_2"])

    count =0
    
    import numpy as np
    
    while True:
        count+=1

        start_time = time.perf_counter()
        scores = px4Score.count_score()
        
        print([f"{score:.1f}" for score in scores])
        nan_indices = np.where(np.isnan(scores))[0]
        print("NaN 值的索引:", nan_indices)
        
        
        end_time = time.perf_counter()

        print(f"第{count}轮 耗时: {end_time - start_time:.4f} 秒")
        
        
        