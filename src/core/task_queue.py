import queue
import threading
import uuid
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from PySide6.QtCore import QObject, Signal
from src.utils.logger import get_logger


logger = get_logger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MediaTask:
    def __init__(
        self,
        task_type: str,
        params: Dict[str, Any],
        name: str = ""
    ):
        self.task_id = str(uuid.uuid4())
        self.task_type = task_type
        self.name = name or f"{task_type}_{self.task_id[:8]}"
        self.params = params.copy()
        self.status = TaskStatus.PENDING
        self.progress = 0.0
        self.progress_message = ""
        self.logs: List[str] = []
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = None
        self.started_at = None
        self.completed_at = None
        
        self._progress_callback: Optional[Callable[[float, str], None]] = None
        self._status_callback: Optional[Callable[[TaskStatus], None]] = None
        self._log_callback: Optional[Callable[[str], None]] = None
    
    def set_callbacks(
        self,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        status_callback: Optional[Callable[[TaskStatus], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ):
        self._progress_callback = progress_callback
        self._status_callback = status_callback
        self._log_callback = log_callback
    
    def update_progress(self, progress: float, message: str = ""):
        self.progress = max(0.0, min(100.0, progress))
        self.progress_message = message
        if self._progress_callback:
            self._progress_callback(self.progress, self.progress_message)
    
    def update_status(self, status: TaskStatus):
        old_status = self.status
        self.status = status
        
        if status == TaskStatus.RUNNING and self.started_at is None:
            import time
            self.started_at = time.time()
        
        if status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            import time
            self.completed_at = time.time()
        
        if self._status_callback:
            self._status_callback(status)
        
        logger.debug(f"任务 {self.task_id} 状态变更: {old_status.value} -> {status.value}")
    
    def add_log(self, log: str):
        self.logs.append(log)
        if self._log_callback:
            self._log_callback(log)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "name": self.name,
            "params": self.params,
            "status": self.status.value,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "logs": self.logs.copy(),
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


class TaskQueueSignals(QObject):
    task_added = Signal(str)
    task_removed = Signal(str)
    task_status_changed = Signal(str, str)
    task_progress_changed = Signal(str, float, str)
    task_log_added = Signal(str, str)
    queue_empty = Signal()
    queue_paused = Signal()
    queue_resumed = Signal()


class TaskQueue:
    _instance: Optional["TaskQueue"] = None
    
    def __new__(cls) -> "TaskQueue":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        
        self._initialized = True
        self._tasks: Dict[str, MediaTask] = {}
        self._pending_queue: queue.Queue = queue.Queue()
        self._paused = False
        self._running = False
        self._current_task: Optional[MediaTask] = None
        self._lock = threading.RLock()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        self.signals = TaskQueueSignals()
        
        logger.info("任务队列初始化完成")
    
    def add_task(self, task: MediaTask) -> str:
        with self._lock:
            import time
            task.created_at = time.time()
            
            self._tasks[task.task_id] = task
            self._pending_queue.put(task.task_id)
            
            task.set_callbacks(
                progress_callback=lambda p, m: self._on_task_progress(task.task_id, p, m),
                status_callback=lambda s: self._on_task_status(task.task_id, s),
                log_callback=lambda l: self._on_task_log(task.task_id, l)
            )
            
            logger.info(f"添加任务: {task.task_id} ({task.name})")
            self.signals.task_added.emit(task.task_id)
            
            self._start_worker()
            
            return task.task_id
    
    def remove_task(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            if task.status == TaskStatus.RUNNING:
                self.cancel_task(task_id)
                return False
            
            if task.status in (TaskStatus.PENDING, TaskStatus.PAUSED):
                del self._tasks[task_id]
                logger.info(f"移除任务: {task_id}")
                self.signals.task_removed.emit(task_id)
                return True
            
            return False
    
    def cancel_task(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                return False
            
            logger.info(f"取消任务: {task_id}")
            task.update_status(TaskStatus.CANCELLED)
            
            if self._current_task == task:
                self._current_task = None
            
            return True
    
    def pause_queue(self) -> None:
        with self._lock:
            if not self._paused:
                self._paused = True
                logger.info("任务队列已暂停")
                self.signals.queue_paused.emit()
    
    def resume_queue(self) -> None:
        with self._lock:
            if self._paused:
                self._paused = False
                logger.info("任务队列已恢复")
                self.signals.queue_resumed.emit()
                self._start_worker()
    
    def get_task(self, task_id: str) -> Optional[MediaTask]:
        with self._lock:
            return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[MediaTask]:
        with self._lock:
            return list(self._tasks.values())
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[MediaTask]:
        with self._lock:
            return [task for task in self._tasks.values() if task.status == status]
    
    def clear_completed(self) -> int:
        with self._lock:
            count = 0
            task_ids_to_remove = [
                task_id for task_id, task in self._tasks.items()
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
            ]
            
            for task_id in task_ids_to_remove:
                del self._tasks[task_id]
                self.signals.task_removed.emit(task_id)
                count += 1
            
            logger.info(f"清理已完成任务: {count} 个")
            return count
    
    def is_paused(self) -> bool:
        with self._lock:
            return self._paused
    
    def is_empty(self) -> bool:
        with self._lock:
            pending_count = self._pending_queue.qsize()
            has_running = self._current_task is not None
            return pending_count == 0 and not has_running
    
    def _start_worker(self) -> None:
        with self._lock:
            if self._running or self._paused:
                return
            
            self._running = True
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()
            logger.info("任务队列工作线程已启动")
    
    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                with self._lock:
                    if self._paused:
                        break
                
                task_id = None
                try:
                    task_id = self._pending_queue.get(timeout=0.5)
                except queue.Empty:
                    pass
                
                if task_id is None:
                    continue
                
                with self._lock:
                    task = self._tasks.get(task_id)
                    if not task or task.status != TaskStatus.PENDING:
                        continue
                    
                    if self._paused:
                        self._pending_queue.put(task_id)
                        break
                    
                    self._current_task = task
                    task.update_status(TaskStatus.RUNNING)
                
                self._execute_task(task)
                
                with self._lock:
                    self._current_task = None
                
                self._pending_queue.task_done()
                
            except Exception as e:
                logger.error(f"任务队列工作线程异常: {e}")
        
        with self._lock:
            self._running = False
            if self.is_empty():
                self.signals.queue_empty.emit()
            logger.info("任务队列工作线程已停止")
    
    def _execute_task(self, task: MediaTask) -> None:
        logger.info(f"开始执行任务: {task.task_id} ({task.name})")
        
        try:
            task.update_progress(0, "准备中...")
            
            task_type = task.task_type
            params = task.params
            
            self._simulate_task_execution(task)
            
            task.update_progress(100, "完成")
            task.update_status(TaskStatus.COMPLETED)
            task.result = {"success": True}
            
            logger.info(f"任务完成: {task.task_id}")
            
        except Exception as e:
            logger.error(f"任务执行失败: {task.task_id}, 错误: {e}")
            task.error = str(e)
            task.update_status(TaskStatus.FAILED)
    
    def _simulate_task_execution(self, task: MediaTask) -> None:
        import time
        total_steps = 100
        for i in range(total_steps):
            with self._lock:
                if task.status == TaskStatus.CANCELLED:
                    raise Exception("任务已取消")
            
            progress = (i + 1) / total_steps * 100
            task.update_progress(progress, f"处理中... {progress:.0f}%")
            time.sleep(0.05)
    
    def _on_task_progress(self, task_id: str, progress: float, message: str) -> None:
        self.signals.task_progress_changed.emit(task_id, progress, message)
    
    def _on_task_status(self, task_id: str, status: TaskStatus) -> None:
        self.signals.task_status_changed.emit(task_id, status.value)
    
    def _on_task_log(self, task_id: str, log: str) -> None:
        self.signals.task_log_added.emit(task_id, log)
    
    def stop(self) -> None:
        with self._lock:
            self._stop_event.set()
            self._paused = True
            
            if self._current_task:
                self.cancel_task(self._current_task.task_id)
        
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)
        
        logger.info("任务队列已停止")
