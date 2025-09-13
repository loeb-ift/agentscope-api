from celery import Celery
from app.core.config import settings
import os

# 创建Celery应用实例
celery_app = Celery(
    "agentscope-api",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.debate_tasks"]
)

# 配置Celery应用
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=settings.TIMEZONE,
    enable_utc=True,
    result_expires=settings.CELERY_RESULT_EXPIRES,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    broker_connection_retry_on_startup=True,
    # 配置任务路由
    task_routes={
        "app.tasks.debate_tasks.run_debate": {
            "queue": "debate_queue",
        },
        "app.tasks.debate_tasks.generate_conclusion": {
            "queue": "conclusion_queue",
        },
        "app.tasks.debate_tasks.notify_debate_completion": {
            "queue": "notification_queue",
        },
    },
    # 配置beat调度器（如果需要定时任务）
    beat_schedule={
        # 可以在这里配置定期清理任务
        # "cleanup-expired-debates": {
        #     "task": "app.tasks.debate_tasks.cleanup_expired_debates",
        #     "schedule": 86400,  # 每天执行一次
        # },
    },
)

# 如果在开发模式下运行，可以启用任务追踪
if settings.DEBUG:
    celery_app.conf.worker_hijack_root_logger = False
    celery_app.conf.worker_log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    celery_app.conf.task_track_started = True

# 确保不会在导入时执行任务
if __name__ == "__main__":
    celery_app.start()