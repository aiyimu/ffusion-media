import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.modules.video_cutter import VideoCutter
from src.core.exceptions import (
    MissingParameterError,
    InvalidParameterError,
    FileNotFoundError,
    FileNotReadableError
)


class TestVideoCutter(unittest.TestCase):
    
    def setUp(self):
        self.cutter = VideoCutter()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.temp_file = self.temp_dir / "test.mp4"
        self.temp_file.touch()
        self.output_dir = self.temp_dir / "output"
        self.output_dir.mkdir()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_default_params(self):
        params = self.cutter.get_default_params()
        
        self.assertIn("input_files", params)
        self.assertIn("output_dir", params)
        self.assertIn("output_format", params)
        self.assertIn("cut_mode", params)
        self.assertIn("time_mode", params)
        self.assertIn("start_time", params)
        self.assertIn("end_time", params)
        self.assertIn("duration", params)
        self.assertIn("use_keyframe_align", params)
        self.assertIn("overwrite", params)
        self.assertIn("output_suffix", params)
        
        self.assertEqual(params["cut_mode"], "lossless")
        self.assertEqual(params["time_mode"], "start_end")
        self.assertEqual(params["output_format"], ".mp4")
    
    def test_validate_params_missing_input_files(self):
        params = self.cutter.get_default_params()
        params["input_files"] = []
        params["output_dir"] = str(self.output_dir)
        params["start_time"] = "0:00:00"
        params["end_time"] = "0:00:10"
        self.cutter.set_params(params)
        
        with self.assertRaises(MissingParameterError):
            self.cutter.validate_params()
    
    def test_validate_params_missing_output_dir(self):
        params = self.cutter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = ""
        params["start_time"] = "0:00:00"
        params["end_time"] = "0:00:10"
        self.cutter.set_params(params)
        
        with self.assertRaises(MissingParameterError):
            self.cutter.validate_params()
    
    def test_validate_params_nonexistent_file(self):
        params = self.cutter.get_default_params()
        params["input_files"] = ["nonexistent.mp4"]
        params["output_dir"] = str(self.output_dir)
        params["start_time"] = "0:00:00"
        params["end_time"] = "0:00:10"
        self.cutter.set_params(params)
        
        with self.assertRaises(FileNotFoundError):
            self.cutter.validate_params()
    
    def test_validate_params_invalid_output_format(self):
        params = self.cutter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["output_format"] = ".xyz"
        params["start_time"] = "0:00:00"
        params["end_time"] = "0:00:10"
        self.cutter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.cutter.validate_params()
    
    def test_validate_params_invalid_cut_mode(self):
        params = self.cutter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["cut_mode"] = "invalid_mode"
        params["start_time"] = "0:00:00"
        params["end_time"] = "0:00:10"
        self.cutter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.cutter.validate_params()
    
    def test_validate_params_invalid_time_mode(self):
        params = self.cutter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["time_mode"] = "invalid_mode"
        params["start_time"] = "0:00:00"
        params["end_time"] = "0:00:10"
        self.cutter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.cutter.validate_params()
    
    def test_validate_params_start_end_time_equal(self):
        params = self.cutter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["time_mode"] = "start_end"
        params["start_time"] = "0:00:10"
        params["end_time"] = "0:00:10"
        self.cutter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.cutter.validate_params()
    
    def test_validate_params_start_end_time_invalid_order(self):
        params = self.cutter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["time_mode"] = "start_end"
        params["start_time"] = "0:00:20"
        params["end_time"] = "0:00:10"
        self.cutter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.cutter.validate_params()
    
    def test_validate_params_start_duration_invalid(self):
        params = self.cutter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["time_mode"] = "start_duration"
        params["start_time"] = "0:00:00"
        params["duration"] = "0:00:00"
        self.cutter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.cutter.validate_params()
    
    def test_validate_params_invalid_time_format(self):
        params = self.cutter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["start_time"] = "invalid_time"
        params["end_time"] = "0:00:10"
        self.cutter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.cutter.validate_params()
    
    def test_get_supported_input_formats(self):
        formats = self.cutter.get_supported_input_formats()
        self.assertIsInstance(formats, list)
        self.assertGreater(len(formats), 0)
    
    def test_get_supported_output_formats(self):
        formats = self.cutter.get_supported_output_formats()
        self.assertIsInstance(formats, list)
        self.assertIn(".mp4", formats)
        self.assertIn(".mkv", formats)
        self.assertIn(".avi", formats)
    
    def test_build_single_command_lossless_start_end(self):
        with patch.object(self.cutter._parser, 'get_media_info') as mock_get_info:
            mock_get_info.return_value = {
                "has_video": True,
                "has_audio": True,
                "duration": 100
            }
            
            input_path = Path("/test/input.mp4")
            output_path = Path("/test/output.mp4")
            media_info = {"has_video": True, "has_audio": True, "duration": 100}
            
            self.cutter.set_params({
                "cut_mode": "lossless",
                "time_mode": "start_end",
                "start_time": "0:00:05",
                "end_time": "0:00:15",
                "use_keyframe_align": True
            })
            
            command = self.cutter._build_single_command(input_path, output_path, media_info)
            
            self.assertIn("-ss", command)
            self.assertIn("0:00:05", command)
            self.assertIn("-i", command)
            self.assertIn("-t", command)
            self.assertIn("10.0", command)
            self.assertIn("-c:v", command)
            self.assertIn("copy", command)
            self.assertIn("-c:a", command)
    
    def test_build_single_command_accurate_start_duration(self):
        with patch.object(self.cutter._parser, 'get_media_info') as mock_get_info:
            mock_get_info.return_value = {
                "has_video": True,
                "has_audio": True,
                "duration": 100
            }
            
            input_path = Path("/test/input.mp4")
            output_path = Path("/test/output.mp4")
            media_info = {"has_video": True, "has_audio": True, "duration": 100}
            
            self.cutter.set_params({
                "cut_mode": "accurate",
                "time_mode": "start_duration",
                "start_time": "0:00:05",
                "duration": "0:00:10",
                "use_keyframe_align": False
            })
            
            command = self.cutter._build_single_command(input_path, output_path, media_info)
            
            self.assertIn("-i", command)
            self.assertIn("-ss", command)
            self.assertIn("0:00:05", command)
            self.assertIn("-t", command)
            self.assertIn("0:00:10", command)
            self.assertIn("-c:v", command)
            self.assertIn("libx264", command)
            self.assertIn("-c:a", command)
            self.assertIn("aac", command)
    
    @patch.object(VideoCutter, 'validate_params')
    @patch.object(VideoCutter, '_build_single_command')
    @patch.object(VideoCutter, '_validate_time_range')
    def test_execute_builds_command(self, mock_validate_time, mock_build_cmd, mock_validate):
        mock_build_cmd.return_value = ["ffmpeg", "-i", "test.mp4", "output.mp4"]
        
        with patch.object(self.cutter._parser, 'get_media_info') as mock_get_info, \
             patch.object(self.cutter._engine, 'build_command') as mock_engine_build, \
             patch.object(self.cutter._engine, 'execute_sync') as mock_execute:
            
            mock_get_info.return_value = {
                "has_video": True,
                "has_audio": True,
                "duration": 100
            }
            mock_engine_build.return_value = ["ffmpeg", "-i", "test.mp4", "output.mp4"]
            mock_execute.return_value = {"success": True}
            
            params = self.cutter.get_default_params()
            params["input_files"] = [str(self.temp_file)]
            params["output_dir"] = str(self.output_dir)
            params["start_time"] = "0:00:00"
            params["end_time"] = "0:00:10"
            self.cutter.set_params(params)
            
            result = self.cutter.execute()
            
            self.assertTrue(result)
    
    def test_set_and_get_params(self):
        params = {
            "input_files": ["video1.mp4", "video2.mp4"],
            "output_dir": "/test/output",
            "output_format": ".mkv",
            "cut_mode": "accurate",
            "time_mode": "start_duration",
            "start_time": "0:00:00",
            "duration": "0:00:30"
        }
        
        self.cutter.set_params(params)
        retrieved = self.cutter.get_params()
        
        self.assertEqual(retrieved["input_files"], ["video1.mp4", "video2.mp4"])
        self.assertEqual(retrieved["output_dir"], "/test/output")
        self.assertEqual(retrieved["output_format"], ".mkv")
        self.assertEqual(retrieved["cut_mode"], "accurate")
        self.assertEqual(retrieved["time_mode"], "start_duration")
    
    def test_reset(self):
        custom_params = {
            "input_files": ["video.mp4"],
            "output_dir": "/test/output",
            "cut_mode": "accurate"
        }
        
        self.cutter.set_params(custom_params)
        self.cutter.reset()
        
        default_params = self.cutter.get_default_params()
        current_params = self.cutter.get_params()
        
        self.assertEqual(current_params, default_params)
        self.assertFalse(self.cutter.is_running())
        self.assertFalse(self.cutter.is_cancelled())
    
    def test_cancel(self):
        self.assertFalse(self.cutter.is_cancelled())
        self.cutter.cancel()
        self.assertTrue(self.cutter.is_cancelled())
        self.cutter.reset()
        self.assertFalse(self.cutter.is_cancelled())


if __name__ == '__main__':
    unittest.main()
