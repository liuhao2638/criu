



./Tools/simulation/jmavsim/jmavsim_run.sh -p 19410 -u -q -o

sudo criu dump -D ~/criu/sih -j -t 5810  --tcp-established --file-locks
sudo criu restore -D ~/criu/sih/ -j --tcp-established

sudo criu dump -D ~/criu/sih1 -j -t 19796 --tcp-established --file-locks
sudo criu restore -D ~/criu/sih1/ -j --tcp-established

sudo criu restore -D ~/criu/sih2/ -j --tcp-established --restore-detached

cd ~/criu & rm -rf ramdisk/* 
mkdir -p ramdisk/px4_working_dir/instance_0

export PX4_SYS_AUTOSTART=10040
export PX4_SIM_SPEED_FACTOR=1000
/home/liuhao/PX4-Autopilot-1.15.4/build/px4_sitl_default/bin/px4 \
-i 0 \
/home/liuhao/PX4-Autopilot-1.15.4/build/px4_sitl_default/etc \
-w /home/liuhao/criu/ramdisk/px4_working_dir/instance_0 \
-s /home/liuhao/PX4-Autopilot-1.15.4/build/px4_sitl_default/etc/init.d-posix/rcS 

mkdir -p ~/criu/ramdisk/criu/checkpoint 
touch file_mappings.txt

sudo criu dump -t 874805 -D ~/criu/ramdisk/criu/checkpoint -j  --tcp-established --file-locks
instance_0 _restore
sudo criu restore -D ~/criu/ramdisk/criu/checkpoint -j \
  --replace-path ~/criu/ramdisk/px4_working_dir/instance_0/dataman=~/criu/ramdisk/px4_working_dir/instance_0_restore/dataman \
  --replace-path ~/criu/ramdisk/px4_working_dir/instance_0/parameters.bson=~/criu/ramdisk/px4_working_dir/instance_0_restore/parameters.bson \
  --replace-path ~/criu/ramdisk/px4_working_dir/instance_0/parameters_backup.bson=~/criu/ramdisk/px4_working_dir/instance_0_restore/parameters_backup.bson


sudo criu dump -D ~/criu/ramdisk/px4_working_dir/criu_img -j -t 963856 --tcp-established --file-locks
sudo criu restore -D ~/criu/ramdisk/px4_working_dir/criu_img -j --tcp-established
sudo criu dump -D ~/criu/ramdisk/px4_working_dir/criu_img1 -j -t 963856 --tcp-established --file-locks

sudo criu restore -D ~/criu/ramdisk/px4_working_dir/criu_img -j -t 962014 --tcp-established
sudo criu restore -D ~/criu/ramdisk/px4_working_dir/criu_img1 -j -t 962015 --tcp-established


x y z
vx vy vz
roll pitch yaw
rollspeed pitchspeed yawspeed

连接px4端口
控制所有无人机起飞
whlie
    改参数
    算分


输入一组需要测试的无人机参数
启动px4
设定直线mission
等待其飞行到稳定状态

对于1000架px4服务器cpu占用90，



mavlink-routerd -e 10.69.46.173:14550 127.0.0.1:14550
sudo ss -tulnp

git log --oneline -n 1 --format="%H"

bash ./PX4SihSim.bash \
/home/ubuntu/Workspace/python/SEGAFUZZ/criu/ramdisk/px4_working_dir \
/home/ubuntu/Workspace/python/SEGAFUZZ/criu/ramdisk/PX4-Autopilot/build/px4_sitl_default \
300 1 True

make px4_sitl sihsim_quadx

#完成px4目录到ramdisk目录的映射
sudo mount -t tmpfs -o size=1G tmpfs /path/to/b
mkdir -p /home/ubuntu/Workspace/python/SEGAFUZZ/criu/ramdisk/px4
sudo mount --bind /home/ubuntu/px4 /home/ubuntu/Workspace/python/SEGAFUZZ/criu/ramdisk/px4

/home/ubuntu/Workspace/python/SEGAFUZZ/criu/ramdisk/px4/PX4-Autopilot-v1.14.4/build/px4_sitl_default/bin/px4-bsondump --instance 0  parameters.bson



sudo criu dump -D ./sih -j --tcp-established --file-locks -t 5105
sudo criu restore -D ./sih -j --tcp-established
# criu
# criu
