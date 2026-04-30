"""
日志配置模块
配置统一的日志记录，支持控制台输出和文件输出
"""
import logging
import sys
from datetime import datetime
import os
import traceback

# 日志级别映射
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

# 默认日志格式
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 创建 logs 目录（放在 backend/ 下，而不是 backend/utils/）
# 获取 backend/ 目录的路径（utils/ 的上一级）
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BACKEND_DIR, "logs")
try:
    os.makedirs(LOGS_DIR, exist_ok=True)
    print(f"✅ 日志目录已创建/存在: {LOGS_DIR}")
except Exception as e:
    print(f"❌ 创建日志目录失败: {e}")
    LOGS_DIR = None


def setup_logging(
    level: str = "info",
    log_file: bool = True,
    log_console: bool = True,
    format_string: str = DEFAULT_FORMAT
) -> logging.Logger:
    """
    配置日志系统
    
    Args:
        level: 日志级别 (debug/info/warning/error/critical)
        log_file: 是否输出到文件
        log_console: 是否输出到控制台
        format_string: 日志格式字符串
    
    Returns:
        配置好的 root logger
    """
    # 获取日志级别
    log_level = LOG_LEVELS.get(level.lower(), logging.INFO)
    
    # 创建 root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 清除已有的 handlers（避免重复添加）
    logger.handlers.clear()
    
    # 创建 formatter
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    
    # 控制台 handler
    if log_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 文件 handler
    if log_file and LOGS_DIR:
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            log_file_path = os.path.join(LOGS_DIR, f"stylemate_{today}.log")
            
            file_handler = logging.FileHandler(
                log_file_path,
                encoding="utf-8",
                mode="a"  # 追加模式
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # 测试写入
            logger.info(f"✅ 日志文件已创建: {log_file_path}")
            print(f"✅ 日志文件: {log_file_path}")
            
        except Exception as e:
            print(f"❌ 创建日志文件失败: {e}")
            traceback.print_exc()
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的 logger
    
    Args:
        name: logger 名称（通常使用 __name__）
    
    Returns:
        配置好的 logger 实例
    """
    return logging.getLogger(name)


# 默认配置：在导入时自动配置
# 如果需要在启动时自定义，可以在 main.py 中调用 setup_logging()
_default_logger = setup_logging(level="info", log_file=True, log_console=True)


if __name__ == "__main__":
    # 测试日志功能
    logger = get_logger(__name__)
    
    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    
    print("✅ 日志配置测试完成，请查看控制台输出和 logs/ 目录下的日志文件")
