import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.core.ffmpeg_engine import FFmpegEngine, FFmpegAsyncTask
from src.core.exceptions import (
    FFmpegNotFoundError,
    InvalidFFmpegCommandError
)


class TestFFmpegEngine(unittest.TestCase):
    
    def setUp(self):
        self.engine = FFmpegEngine()
    
    def test_singleton_instance(self):
        engine1 = FFmpegEngine()
        engine2 = FFmpegEngine()
        self.assertIs(engine1, engine2)
    
    @patch('src.core.ffmpeg_engine.get_ffmpeg_path')
    def test_locate_ffmpeg_success(self, mock_get_path):
        mock_path = Path("/fake/path/ffmpeg")
        mock_get_path.return_value = mock_path
        engine = FFmpegEngine()
        self.assertEqual(engine.get_ffmpeg_path(), mock_path)
    
    def test_set_ffmpeg_path_invalid(self):
        with self.assertRaises(FFmpegNotFoundError):
            self.engine.set_ffmpeg_path("/invalid/path/ffmpeg")
    
    @patch('src.core.ffmpeg_engine.FFmpegEngine._check_ffmpeg_available')
    def test_build_command(self, mock_check):
        with patch.object(self.engine, '_ffmpeg_path', Path("/fake/ffmpeg")):
            cmd = self.engine.build_command("-i", "input.mp4", "output.mp4")
            self.assertEqual(cmd[0], "/fake/ffmpeg")
            self.assertEqual(cmd[1], "-y")
            self.assertEqual(cmd[2], "-i")
            self.assertEqual(cmd[3], "input.mp4")
            self.assertEqual(cmd[4], "output.mp4")
    
    def test_build_command_without_ffmpeg(self):
        with patch.object(self.engine, '_ffmpeg_path', None):
            with self.assertRaises(FFmpegNotFoundError):
                self.engine.build_command("-i", "input.mp4")
    
    @patch('subprocess.run')
    @patch('src.core.ffmpeg_engine.FFmpegEngine._check_ffmpeg_available')
    def test_execute_sync_success(self, mock_check, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        with patch.object(self.engine, '_ffmpeg_path', Path("/fake/ffmpeg")):
            result = self.engine.execute_sync(["/fake/ffmpeg", "-i", "input.mp4"])
            self.assertTrue(result["success"])
            self.assertEqual(result["returncode"], 0)
    
    @patch('subprocess.run')
    @patch('src.core.ffmpeg_engine.FFmpegEngine._check_ffmpeg_available')
    def test_execute_sync_failure(self, mock_check, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"
        mock_run.return_value = mock_result
        
        from src.core.exceptions import FFmpegExecutionError
        with patch.object(self.engine, '_ffmpeg_path', Path("/fake/ffmpeg")):
            with self.assertRaises(FFmpegExecutionError):
                self.engine.execute_sync(["/fake/ffmpeg", "-i", "input.mp4"])
    
    def test_execute_sync_invalid_command(self):
        with self.assertRaises(InvalidFFmpegCommandError):
            self.engine.execute_sync(["invalid", "command"])


class TestFFmpegAsyncTask(unittest.TestCase):
    
    def test_initialization(self):
        task = FFmpegAsyncTask(["/fake/ffmpeg", "-i", "input.mp4"], 60.0)
        self.assertEqual(task.duration, 60.0)
        self.assertFalse(task.is_cancelled())
    
    def test_cancel(self):
        task = FFmpegAsyncTask(["/fake/ffmpeg", "-i", "input.mp4"])
        task.cancel()
        self.assertTrue(task.is_cancelled())


if __name__ == "__main__":
    unittest.main()
