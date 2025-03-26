from pymavlink import mavutil
import time
import math


def get_current_state(pos_msg, att_msg):
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


def get_setpoints(pos_target_msg, att_target_msg):
    """
    从 POSITION_TARGET_LOCAL_NED 和 ATTITUDE_TARGET 消息中提取设定值。

    :param pos_target_msg: POSITION_TARGET_LOCAL_NED 消息
    :param att_target_msg: ATTITUDE_TARGET 消息
    :return: 返回设定值的字典
    """
    return {
        "position_setpoint": {"x": pos_target_msg.x, "y": pos_target_msg.y, "z": pos_target_msg.z},
        "velocity_setpoint": {"vx": pos_target_msg.vx, "vy": pos_target_msg.vy, "vz": pos_target_msg.vz},
        "attitude_setpoint": {"roll": att_target_msg.body_roll_rate, "pitch": att_target_msg.body_pitch_rate, "yaw": att_target_msg.body_yaw_rate},
        "angular_velocity_setpoint": {
            "rollspeed": att_target_msg.body_roll_rate,
            "pitchspeed": att_target_msg.body_pitch_rate,
            "yawspeed": att_target_msg.body_yaw_rate,
        },
    }


def calculate_difference(current_state, setpoint):
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


def normalize_score(value, min_value, max_value):
    """
    将单个维度的差值归一化到0-100分。

    :param value: 当前维度的差值
    :param min_value: 差值的最小值
    :param max_value: 差值的最大值
    :return: 归一化后的分数（0-100）
    """
    if value < min_value:
        return 0
    # elif value > max_value:
    #     return 100
    else:
        return 100 * (value - min_value) / (max_value - min_value)


def calculate_total_score(difference, min_values, max_values, weights):
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
            value = abs(difference[key][subkey])  # 取绝对值
            score = normalize_score(value, min_values[key][subkey], max_values[key][subkey])
            total_score += score * weights[key][subkey]

    return total_score / total_weight  # 归一化到 0-100 之间


def monitor_px4_state(master):
    """
    监听PX4消息流，计算每一秒内差值的平均值，并输出分数。
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
        # 获取 LOCAL_POSITION_NED 消息（位置和速度）
        pos_msg = master.recv_match(type="LOCAL_POSITION_NED", blocking=True, timeout=1)
        # 获取 ATTITUDE 消息（姿态和角速度）
        att_msg = master.recv_match(type="ATTITUDE", blocking=True, timeout=1)
        # 获取 POSITION_TARGET_LOCAL_NED 消息（位置和速度设定值）
        pos_target_msg = master.recv_match(type="POSITION_TARGET_LOCAL_NED", blocking=True, timeout=1)
        # 获取 ATTITUDE_TARGET 消息（姿态和角速度设定值）
        att_target_msg = master.recv_match(type="ATTITUDE_TARGET", blocking=True, timeout=1)

        # 当所有消息都收到后，计算差值
        # if all(var in locals() for var in ["pos_msg", "att_msg", "pos_target_msg", "att_target_msg"]):
        # 获取当前状态和设定值
        current_state = get_current_state(pos_msg, att_msg)
        setpoint = get_setpoints(pos_target_msg, att_target_msg)

        # 计算差值
        difference = calculate_difference(current_state, setpoint)

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
                total_score = calculate_total_score(average_difference, min_values, max_values, weights)

                # 输出平均值和总分
                print("1秒内差值的平均值:")
                for key in average_difference:
                    print(f"{key}: {average_difference[key]}")
                print(f"总分: {total_score:.2f}")

            # 重置累加器和计数器
            total_difference = {
                "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                "velocity": {"vx": 0.0, "vy": 0.0, "vz": 0.0},
                "attitude": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0},
                "angular_velocity": {"rollspeed": 0.0, "pitchspeed": 0.0, "yawspeed": 0.0},
            }
            count = 0
            start_time = time.time()


if __name__ == "__main__":
    # 连接到仿真环境中的无人机（使用 14540 端口）
    master = mavutil.mavlink_connection("udp:127.0.0.1:60000")

    # 开始监听PX4消息流
    monitor_px4_state(master)
