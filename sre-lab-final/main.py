# -*- coding: utf-8 -*-
"""
SRE 主机巡检工具 v1.0（作品1雏形）
整合：psutil采集 + yaml配置外置 + argparse命令行 + 阈值告警 + 滚动日志

这是你 W2 一周学习的最终产物——一个能跑在 Windows/Linux 上的真实巡检脚本。
简历上可以写：
  "基于 Python 的主机巡检工具，支持 psutil 指标采集、yaml 配置外置、
   阈值告警分级、滚动日志输出、命令行参数覆盖配置。"
"""
import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import psutil
import yaml


# ---------- 1. 日志配置（logging ≈ Java Log4j）----------
def setup_logger() -> logging.Logger:
    logger = logging.getLogger("sre-inspect")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # 控制台
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # 文件滚动：单个文件 5MB，保留 5 个备份
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    fh = RotatingFileHandler(log_dir / "sre.log", maxBytes=5*1024*1024,
                             backupCount=5, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger


# ---------- 2. 读 yaml 配置（≈ Java application.yml）----------
def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------- 3. psutil 采集（≈ Java OSHI / SIGAR）----------
def collect(top_n: int) -> dict:
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disks = []
    for p in psutil.disk_partitions():
        try:
            u = psutil.disk_usage(p.mountpoint)
            disks.append({"mount": p.mountpoint, "pct": u.percent})
        except PermissionError:
            pass

    procs = []
    for proc in psutil.process_iter(["name", "cpu_percent"]):
        try:
            procs.append({"name": proc.info["name"], "cpu": proc.info["cpu_percent"] or 0})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs = sorted(procs, key=lambda x: x["cpu"], reverse=True)[:top_n]

    return {
        "cpu_pct": cpu,
        "mem_pct": mem,
        "disks": disks,
        "top_processes": procs,
    }


# ---------- 4. 阈值判断（告警分级）----------
def check_alerts(metrics: dict, cfg: dict) -> list:
    th = cfg["thresholds"]
    alerts = []
    if metrics["cpu_pct"] > th["cpu_warn_pct"]:
        alerts.append(f"CPU {metrics['cpu_pct']}% 超阈值 {th['cpu_warn_pct']}%")
    if metrics["mem_pct"] > th["mem_warn_pct"]:
        alerts.append(f"内存 {metrics['mem_pct']}% 超阈值 {th['mem_warn_pct']}%")
    for d in metrics["disks"]:
        if d["pct"] > th["disk_warn_pct"]:
            alerts.append(f"磁盘 {d['mount']} {d['pct']}% 超阈值 {th['disk_warn_pct']}%")
    return alerts


# ---------- 5. 主流程 ----------
def main():
    parser = argparse.ArgumentParser(description="SRE 主机巡检工具 v1.0")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--top", type=int, default=None, help="进程 Top N（覆盖配置）")
    parser.add_argument("--cpu-warn", type=float, default=None, help="CPU 告警阈值（覆盖配置）")
    parser.add_argument("--mem-warn", type=float, default=None, help="内存告警阈值（覆盖配置）")
    args = parser.parse_args()

    log = setup_logger()
    cfg = load_config(args.config)

    # 命令行参数覆盖 yaml（≈ Spring Boot 的 --args 覆盖 application.yml）
    if args.top is not None:
        cfg["inspect"]["top_n"] = args.top
    if args.cpu_warn is not None:
        cfg["thresholds"]["cpu_warn_pct"] = args.cpu_warn
    if args.mem_warn is not None:
        cfg["thresholds"]["mem_warn_pct"] = args.mem_warn

    log.info("=" * 50)
    log.info("开始主机巡检")

    # 采集
    m = collect(cfg["inspect"]["top_n"])
    log.info(f"CPU 使用率: {m['cpu_pct']}%")
    log.info(f"内存使用率: {m['mem_pct']}%")
    for d in m["disks"]:
        log.info(f"磁盘 {d['mount']}: {d['pct']}%")
    log.info(f"进程 Top{cfg['inspect']['top_n']}:")
    for p in m["top_processes"]:
        log.info(f"  - {p['name']}: {p['cpu']:.1f}%")

    # 告警
    alerts = check_alerts(m, cfg)
    if alerts:
        for a in alerts:
            log.warning(f"[告警] {a}")
    else:
        log.info("[OK] 各项指标均在阈值内")

    log.info("巡检结束")
    log.info("=" * 50)


if __name__ == "__main__":
    main()
