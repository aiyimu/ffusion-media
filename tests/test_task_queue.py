import unittest
import time
from src.core.task_queue import TaskQueue, MediaTask, TaskStatus


class TestMediaTask(unittest.TestCase):
    
    def test_task_creation(self):
        task = MediaTask("convert", {"input": "in.mp4", "output": "out.mp4"})
        self.assertIsNotNone(task.task_id)
        self.assertEqual(task.task_type, "convert")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.progress, 0.0)
    
    def test_task_with_name(self):
        task = MediaTask("cut", {}, "My Custom Task")
        self.assertEqual(task.name, "My Custom Task")
    
    def test_update_progress(self):
        task = MediaTask("convert", {})
        task.update_progress(50.0, "Halfway done")
        self.assertEqual(task.progress, 50.0)
        self.assertEqual(task.progress_message, "Halfway done")
    
    def test_update_progress_clamped(self):
        task = MediaTask("convert", {})
        task.update_progress(-10.0)
        self.assertEqual(task.progress, 0.0)
        task.update_progress(150.0)
        self.assertEqual(task.progress, 100.0)
    
    def test_update_status(self):
        task = MediaTask("convert", {})
        task.update_status(TaskStatus.RUNNING)
        self.assertEqual(task.status, TaskStatus.RUNNING)
        self.assertIsNotNone(task.started_at)
    
    def test_add_log(self):
        task = MediaTask("convert", {})
        task.add_log("First log")
        task.add_log("Second log")
        self.assertEqual(len(task.logs), 2)
        self.assertEqual(task.logs[0], "First log")
    
    def test_to_dict(self):
        task = MediaTask("convert", {"param": "value"})
        task_dict = task.to_dict()
        self.assertEqual(task_dict["task_id"], task.task_id)
        self.assertEqual(task_dict["task_type"], "convert")
        self.assertEqual(task_dict["params"]["param"], "value")
        self.assertEqual(task_dict["status"], "pending")


class TestTaskQueue(unittest.TestCase):
    
    def setUp(self):
        self.queue = TaskQueue()
    
    def test_singleton_instance(self):
        queue1 = TaskQueue()
        queue2 = TaskQueue()
        self.assertIs(queue1, queue2)
    
    def test_add_task(self):
        task = MediaTask("convert", {})
        task_id = self.queue.add_task(task)
        self.assertEqual(task_id, task.task_id)
        retrieved_task = self.queue.get_task(task_id)
        self.assertIsNotNone(retrieved_task)
        self.assertEqual(retrieved_task.task_id, task_id)
    
    def test_get_all_tasks(self):
        task1 = MediaTask("convert", {})
        task2 = MediaTask("cut", {})
        self.queue.add_task(task1)
        self.queue.add_task(task2)
        tasks = self.queue.get_all_tasks()
        self.assertEqual(len(tasks), 2)
    
    def test_get_tasks_by_status(self):
        task1 = MediaTask("convert", {})
        task2 = MediaTask("cut", {})
        self.queue.add_task(task1)
        self.queue.add_task(task2)
        pending_tasks = self.queue.get_tasks_by_status(TaskStatus.PENDING)
        self.assertEqual(len(pending_tasks), 2)
    
    def test_cancel_task(self):
        task = MediaTask("convert", {})
        task_id = self.queue.add_task(task)
        result = self.queue.cancel_task(task_id)
        self.assertTrue(result)
        cancelled_task = self.queue.get_task(task_id)
        self.assertEqual(cancelled_task.status, TaskStatus.CANCELLED)
    
    def test_pause_and_resume_queue(self):
        self.assertFalse(self.queue.is_paused())
        self.queue.pause_queue()
        self.assertTrue(self.queue.is_paused())
        self.queue.resume_queue()
        self.assertFalse(self.queue.is_paused())
    
    def test_clear_completed(self):
        task1 = MediaTask("convert", {})
        task2 = MediaTask("cut", {})
        self.queue.add_task(task1)
        self.queue.add_task(task2)
        
        task1.update_status(TaskStatus.COMPLETED)
        
        count = self.queue.clear_completed()
        self.assertEqual(count, 1)
        
        remaining_tasks = self.queue.get_all_tasks()
        self.assertEqual(len(remaining_tasks), 1)
        self.assertEqual(remaining_tasks[0].task_id, task2.task_id)
    
    def test_is_empty(self):
        self.assertTrue(self.queue.is_empty())
        task = MediaTask("convert", {})
        self.queue.add_task(task)
        self.assertFalse(self.queue.is_empty())


if __name__ == "__main__":
    unittest.main()
