#!/bin/bash

# PX4SihSim.bash
# 该脚本配置PX4仿真环境的参数，包括构建目录、工作目录、实例数量、模拟速度和是否以守护进程运行
px4_working_dir=$1
px4_build_dir=$2
instance_count=$3
sim_speed=$4    
is_daemon=$5    

# px4_working_dir="/home/ubuntu/Workspace/python/SEGAFUZZ/criu/ramdisk/px4_working_dir"
# px4_build_dir="/home/ubuntu/Workspace/python/SEGAFUZZ/criu/ramdisk/PX4-Autopilot/build/px4_sitl_default"
# instance_count=1000
# sim_speed=1
# is_daemon=True   

# echo $px4_build_dir
# echo $px4_working_dir

# 清理旧目录和进程
# echo "清理工作目录和现有px4进程..."
rm -rf "${px4_working_dir}"
mkdir -p "${px4_working_dir}/instance"
mkdir -p "${px4_working_dir}/log"
killall px4 2>/dev/null

# 存储进程ID的数组
declare -a pids=()

# 定义启动单个实例的函数
start_single_sih_sitl() {
    local instance_num=$1
    local working_dir="${px4_working_dir}/instance/instance_${instance_num}"
    # local working_dir="${px4_working_dir}/instance_${instance_num}"
    mkdir -p "$working_dir"

    # 设置环境变量
    export PX4_SYS_AUTOSTART=10040
    export PX4_SIMULATOR="sihsim"
    export PX4_SIM_SPEED_FACTOR=$sim_speed

    # 构建命令参数
    local cmd=(
        "${px4_build_dir}/bin/px4"
        "-i" "$instance_num"
        "-s" "${px4_build_dir}/etc/init.d-posix/rcS"
        "-w" "$working_dir"
        "${px4_build_dir}/etc"
    )
    # 启动进程并重定向输出
    if [ "$is_daemon" = "True" ]; then
        cmd+=("-d")
        "${cmd[@]}" > "${px4_working_dir}/log/$instance_num.log" 2>&1 &
    else
        "${cmd[@]}" &
    fi
    # 记录进程ID $!获取最近一个后台进程的 PID。
    pids[$instance_num]=$!

    # # 等待1秒钟
    # sleep 10
        
    # # 调用check
    # local check=(
    #     "${px4_build_dir}/bin/px4-commander"
    #     "--instance" "$instance_num" 
    #     "check"
    # )
    # # 执行check并接收返回结果
    # local output="$("${check[@]}")"

    # # 判断输出中是否包含 "OK" 或 "FAILED"
    # if [[ "$output" == *"OK"* ]]; then
    #     echo "检查成功: $output"
    #     # 退出循环
    # elif [[ "$output" == *"FAILED"* ]]; then
    #     echo "检查失败: $output 实例：$instance_num"
    #     rm -rf "${working_dir}"
    #     kill "${pids[$instance_num]}"
    # fi

    # # 循环启动px4直到仿真正确执行
    # while true; do

    #     # 启动进程并重定向输出
    #     if [ "$is_daemon" = "True" ]; then
    #         cmd+=("-d")
    #         "${cmd[@]}" > "${px4_working_dir}/log/$instance_num.log" 2>&1 &
    #     else
    #         "${cmd[@]}" &
    #     fi
    #     # 记录进程ID $!获取最近一个后台进程的 PID。
    #     pids[$instance_num]=$!

    #     # 等待1秒钟
    #     sleep 3
        
    #     # 调用check
    #     local check=(
    #         "${px4_build_dir}/bin/px4-commander"
    #         "--instance" "$instance_num" 
    #         "check"
    #     )
    #     # 执行check并接收返回结果
    #     local output="$("${check[@]}")"

    #     # 判断输出中是否包含 "OK" 或 "FAILED"
    #     if [[ "$output" == *"OK"* ]]; then
    #         echo "检查成功: $output"
    #         # 退出循环
    #         break
    #     elif [[ "$output" == *"FAILED"* ]]; then
    #         echo "检查失败: $output 实例：$instance_num"
    #         rm -rf "${working_dir}"
    #         kill "${pids[$instance_num]}"
    #     fi
        
    #     break
    # done
}

check_single_sih_sitl() {
    local instance_num=$1
    local working_dir="${px4_working_dir}/instance/instance_${instance_num}"

    local cmd=(
        "${px4_build_dir}/bin/px4-commander"
        "--instance" "$instance_num" 
        "check"
    )
    # 执行check并接收返回结果
    local output="$("${cmd[@]}")"

    # 判断输出中是否包含 "OK" 或 "FAILED"
    if [[ "$output" == *"OK"* ]]; then
        echo "检查成功: $output"
    elif [[ "$output" == *"FAILED"* ]]; then
        echo "检查失败: $output 实例：$instance_num"
    fi
}

# # 启动所有实例
# # echo "启动 ${instance_count} 个PX4实例..."
# for ((i=0; i<instance_count; i++)); do
#     start_single_sih_sitl $i &
# done
# # 等待所有后台任务完成
# wait
# 启动所有实例
# echo "启动 ${instance_count} 个PX4实例..."
for ((i=0; i<instance_count; i++)); do
    start_single_sih_sitl $i
done
# 等待所有后台任务完成

# echo "检查PX4实例..."
# for ((i=0; i<instance_count; i++)); do
#     check_single_sih_sitl $i &
# done
# echo "检查完成"

echo ${pids[*]}


# # 清理函数
# cleanup() {
#     echo -e "\n检测到 Ctrl+C，清理px4实例..."
#     for pid in "${pids[@]}"; do
#         kill "$pid" 2>/dev/null
#     done
#     wait
#     echo "程序已退出"
#     exit 0
# }

# # 注册信号处理
# trap cleanup INT

# # 保持主进程运行
# echo "运行中，按 Ctrl+C 退出..."
# while true; do
#     sleep 1
# done