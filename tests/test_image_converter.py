import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.modules.image_converter import ImageConverter
from src.core.exceptions import (
    MissingParameterError,
    InvalidParameterError,
    FileNotFoundError,
    FileNotReadableError
)


class TestImageConverter(unittest.TestCase):
    
    def setUp(self):
        self.converter = ImageConverter()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.temp_file = self.temp_dir / "test.mp4"
        self.temp_file.touch()
        self.output_dir = self.temp_dir / "output"
        self.output_dir.mkdir()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_default_params(self):
        params = self.converter.get_default_params()
        
        self.assertIn("input_files", params)
        self.assertIn("output_dir", params)
        self.assertIn("process_mode", params)
        self.assertIn("image_format", params)
        self.assertIn("image_quality", params)
        self.assertIn("extract_mode", params)
        self.assertIn("extract_fps", params)
        self.assertIn("extract_interval", params)
        self.assertIn("extract_total_frames", params)
        self.assertIn("video_fps", params)
        self.assertIn("video_duration", params)
        self.assertIn("gif_fps", params)
        self.assertIn("gif_loop", params)
        self.assertIn("gif_quality", params)
        self.assertIn("width", params)
        self.assertIn("height", params)
        
        self.assertEqual(params["process_mode"], "extract_frames")
        self.assertEqual(params["image_format"], ".jpg")
        self.assertEqual(params["image_quality"], 80)
    
    def test_validate_params_missing_input_files(self):
        params = self.converter.get_default_params()
        params["input_files"] = []
        params["output_dir"] = str(self.output_dir)
        self.converter.set_params(params)
        
        with self.assertRaises(MissingParameterError):
            self.converter.validate_params()
    
    def test_validate_params_missing_output_dir(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = ""
        self.converter.set_params(params)
        
        with self.assertRaises(MissingParameterError):
            self.converter.validate_params()
    
    def test_validate_params_nonexistent_file(self):
        params = self.converter.get_default_params()
        params["input_files"] = ["nonexistent.mp4"]
        params["output_dir"] = str(self.output_dir)
        self.converter.set_params(params)
        
        with self.assertRaises(FileNotFoundError):
            self.converter.validate_params()
    
    def test_validate_params_invalid_process_mode(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "invalid_mode"
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_extract_invalid_image_format(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "extract_frames"
        params["image_format"] = ".xyz"
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_extract_invalid_extract_mode(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "extract_frames"
        params["extract_mode"] = "invalid_mode"
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_extract_fps_out_of_range(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "extract_frames"
        params["extract_mode"] = "fps"
        params["extract_fps"] = 200
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_extract_interval_out_of_range(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "extract_frames"
        params["extract_mode"] = "interval"
        params["extract_interval"] = 5000
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_extract_total_frames_out_of_range(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "extract_frames"
        params["extract_mode"] = "total"
        params["extract_total_frames"] = 20000
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_extract_quality_out_of_range(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "extract_frames"
        params["image_quality"] = 150
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_images_to_video_fps_out_of_range(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "images_to_video"
        params["video_fps"] = 200
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_video_to_gif_fps_out_of_range(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "video_to_gif"
        params["gif_fps"] = 100
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_video_to_gif_loop_out_of_range(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "video_to_gif"
        params["gif_loop"] = 100000
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_image_to_video_duration_out_of_range(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "image_to_video"
        params["video_duration"] = 10000
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_get_supported_input_formats(self):
        formats = self.converter.get_supported_input_formats()
        self.assertIsInstance(formats, list)
        self.assertGreater(len(formats), 0)
    
    def test_get_supported_output_formats(self):
        formats = self.converter.get_supported_output_formats()
        self.assertIsInstance(formats, list)
        self.assertIn(".jpg", formats)
        self.assertIn(".png", formats)
        self.assertIn(".mp4", formats)
        self.assertIn(".mkv", formats)
    
    def test_build_extract_frames_command_fps_mode(self):
        with patch.object(self.converter._parser, 'get_media_info') as mock_get_info:
            mock_get_info.return_value = {
                "has_video": True,
                "has_audio": True,
                "duration": 100
            }
            
            input_path = Path("/test/input.mp4")
            output_dir = Path("/test/output")
            media_info = {"has_video": True, "has_audio": True, "duration": 100}
            
            self.converter.set_params({
                "process_mode": "extract_frames",
                "image_format": ".jpg",
                "extract_mode": "fps",
                "extract_fps": 1,
                "image_quality": 80
            })
            
            command = self.converter._build_extract_frames_command(input_path, output_dir, media_info)
            
            self.assertIn("-i", command)
            self.assertIn("-vf", command)
            self.assertIn("fps=1", command)
            self.assertIn("-q:v", command)
    
    def test_build_extract_frames_command_interval_mode(self):
        with patch.object(self.converter._parser, 'get_media_info') as mock_get_info:
            mock_get_info.return_value = {
                "has_video": True,
                "has_audio": True,
                "duration": 100
            }
            
            input_path = Path("/test/input.mp4")
            output_dir = Path("/test/output")
            media_info = {"has_video": True, "has_audio": True, "duration": 100}
            
            self.converter.set_params({
                "process_mode": "extract_frames",
                "image_format": ".jpg",
                "extract_mode": "interval",
                "extract_interval": 2.0,
                "image_quality": 80
            })
            
            command = self.converter._build_extract_frames_command(input_path, output_dir, media_info)
            
            self.assertIn("-i", command)
            self.assertIn("-vf", command)
            self.assertIn("fps=1/2.0", command)
    
    def test_build_video_to_gif_command(self):
        with patch.object(self.converter._parser, 'get_media_info') as mock_get_info:
            mock_get_info.return_value = {
                "has_video": True,
                "has_audio": True,
                "duration": 100
            }
            
            input_path = Path("/test/input.mp4")
            output_path = Path("/test/output.gif")
            media_info = {"has_video": True, "has_audio": True, "duration": 100}
            
            self.converter.set_params({
                "process_mode": "video_to_gif",
                "gif_fps": 10,
                "gif_loop": 0,
                "gif_quality": 80
            })
            
            command = self.converter._build_video_to_gif_command(input_path, output_path, media_info)
            
            self.assertIn("-i", command)
            self.assertIn("-vf", command)
            self.assertIn("fps=10", command)
            self.assertIn("-loop", command)
    
    def test_build_image_to_video_command(self):
        with patch.object(self.converter._parser, 'get_media_info') as mock_get_info:
            mock_get_info.return_value = {
                "has_video": False,
                "has_audio": False,
                "duration": 0
            }
            
            input_path = Path("/test/input.jpg")
            output_path = Path("/test/output.mp4")
            media_info = {"has_video": False, "has_audio": False, "duration": 0}
            
            self.converter.set_params({
                "process_mode": "image_to_video",
                "video_duration": 5.0,
                "video_fps": 30
            })
            
            command = self.converter._build_image_to_video_command(input_path, output_path, media_info)
            
            self.assertIn("-loop", command)
            self.assertIn("-i", command)
            self.assertIn("-t", command)
            self.assertIn("5.0", command)
            self.assertIn("-r", command)
            self.assertIn("30", command)
    
    @patch.object(ImageConverter, 'validate_params')
    @patch.object(ImageConverter, '_build_single_command')
    def test_execute_builds_command(self, mock_build_cmd, mock_validate):
        mock_build_cmd.return_value = ["ffmpeg", "-i", "test.mp4", "output.jpg"]
        
        with patch.object(self.converter._parser, 'get_media_info') as mock_get_info, \
             patch.object(self.converter._engine, 'build_command') as mock_engine_build, \
             patch.object(self.converter._engine, 'execute_sync') as mock_execute:
            
            mock_get_info.return_value = {
                "has_video": True,
                "has_audio": True,
                "duration": 100
            }
            mock_engine_build.return_value = ["ffmpeg", "-i", "test.mp4", "output.jpg"]
            mock_execute.return_value = {"success": True}
            
            params = self.converter.get_default_params()
            params["input_files"] = [str(self.temp_file)]
            params["output_dir"] = str(self.output_dir)
            self.converter.set_params(params)
            
            result = self.converter.execute()
            
            self.assertTrue(result)
    
    def test_set_and_get_params(self):
        params = {
            "input_files": ["video1.mp4"],
            "output_dir": "/test/output",
            "process_mode": "extract_frames",
            "image_format": ".png",
            "extract_fps": 2
        }
        
        self.converter.set_params(params)
        retrieved = self.converter.get_params()
        
        self.assertEqual(retrieved["input_files"], ["video1.mp4"])
        self.assertEqual(retrieved["output_dir"], "/test/output")
        self.assertEqual(retrieved["process_mode"], "extract_frames")
        self.assertEqual(retrieved["image_format"], ".png")
        self.assertEqual(retrieved["extract_fps"], 2)
    
    def test_reset(self):
        custom_params = {
            "input_files": ["video.mp4"],
            "output_dir": "/test/output",
            "process_mode": "video_to_gif"
        }
        
        self.converter.set_params(custom_params)
        self.converter.reset()
        
        default_params = self.converter.get_default_params()
        current_params = self.converter.get_params()
        
        self.assertEqual(current_params, default_params)
        self.assertFalse(self.converter.is_running())
        self.assertFalse(self.converter.is_cancelled())
    
    def test_cancel(self):
        self.assertFalse(self.converter.is_cancelled())
        self.converter.cancel()
        self.assertTrue(self.converter.is_cancelled())
        self.converter.reset()
        self.assertFalse(self.converter.is_cancelled())


if __name__ == '__main__':
    unittest.main()
