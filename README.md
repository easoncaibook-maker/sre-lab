# SRE Lab - 主机巡检自动化工具

## 项目简介
一个轻量级 Linux 主机巡检脚本，用于监控系统关键指标（CPU、内存、磁盘、Top 进程），支持阈值告警、日志记录和定时执行。

## 技术栈
- Python 3 + psutil
- systemd 服务管理
- Shell 脚本（备份 + 日志归档）
- Linux 权限最小化实践

## 核心功能
- 主机指标采集与阈值告警
- 日志轮转与持久化
- 定时任务自动化（crontab）
- 备份策略与旧文件自动清理

## 部署方式
# 先装epel源（Python3在epel里）
yum install -y epel-release

# 装git、python3、pip、tcpdump
yum install -y git python3 python3-pip tcpdump

# 验证
python3 --version
git --version

cd /opt
git clone https://github.com/easoncaibook-maker/sre-lab.git
cd sre-lab
ls -la

cd /opt/sre-lab/sre-lab-final

# 装Python依赖
pip3 install psutil pyyaml

# 跑一下
python3 main.py

