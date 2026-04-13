import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.modules.format_converter import FormatConverter
from src.core.exceptions import (
    MissingParameterError,
    InvalidParameterError,
    FileNotFoundError,
    FileNotReadableError
)


class TestFormatConverter(unittest.TestCase):
    
    def setUp(self):
        self.converter = FormatConverter()
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
        self.assertIn("output_format", params)
        self.assertIn("use_stream_copy", params)
        self.assertIn("video_encoder", params)
        self.assertIn("audio_encoder", params)
        self.assertIn("width", params)
        self.assertIn("height", params)
        self.assertIn("frame_rate", params)
        self.assertIn("video_bitrate", params)
        self.assertIn("audio_bitrate", params)
        self.assertIn("audio_channels", params)
        self.assertIn("overwrite", params)
        
        self.assertEqual(params["use_stream_copy"], True)
        self.assertEqual(params["output_format"], ".mp4")
    
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
    
    def test_validate_params_invalid_output_format(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["output_format"] = ".xyz"
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_invalid_video_encoder(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["use_stream_copy"] = False
        params["video_encoder"] = "invalid_encoder"
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_invalid_audio_encoder(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["use_stream_copy"] = False
        params["audio_encoder"] = "invalid_encoder"
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_negative_width(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["width"] = -100
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_negative_height(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["height"] = -100
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_negative_frame_rate(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["frame_rate"] = -30
        self.converter.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.converter.validate_params()
    
    def test_validate_params_negative_audio_channels(self):
        params = self.converter.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["audio_channels"] = -2
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
        self.assertIn(".mp4", formats)
        self.assertIn(".mkv", formats)
        self.assertIn(".mp3", formats)
        self.assertIn(".wav", formats)
    
    def test_build_single_command_stream_copy(self):
        with patch.object(self.converter._parser, 'get_media_info') as mock_get_info:
            mock_get_info.return_value = {
                "has_video": True,
                "has_audio": True,
                "duration": 100
            }
            
            input_path = Path("/test/input.mp4")
            output_path = Path("/test/output.mp4")
            media_info = {"has_video": True, "has_audio": True, "duration": 100}
            
            self.converter.set_params({
                "use_stream_copy": True
            })
            
            command = self.converter._build_single_command(input_path, output_path, media_info)
            
            self.assertIn("-i", command)
            self.assertIn("-c:v", command)
            self.assertIn("copy", command)
            self.assertIn("-c:a", command)
    
    def test_build_single_command_reencode(self):
        with patch.object(self.converter._parser, 'get_media_info') as mock_get_info:
            mock_get_info.return_value = {
                "has_video": True,
                "has_audio": True,
                "duration": 100
            }
            
            input_path = Path("/test/input.mp4")
            output_path = Path("/test/output.mp4")
            media_info = {"has_video": True, "has_audio": True, "duration": 100}
            
            self.converter.set_params({
                "use_stream_copy": False,
                "video_encoder": "libx264",
                "audio_encoder": "aac",
                "width": 1280,
                "height": 720,
                "frame_rate": 30,
                "video_bitrate": "5M",
                "audio_bitrate": "192k",
                "audio_channels": 2
            })
            
            command = self.converter._build_single_command(input_path, output_path, media_info)
            
            self.assertIn("-i", command)
            self.assertIn("-c:v", command)
            self.assertIn("libx264", command)
            self.assertIn("-c:a", command)
            self.assertIn("aac", command)
            self.assertIn("-vf", command)
            self.assertIn("scale=1280:720", command)
            self.assertIn("-r", command)
            self.assertIn("30", command)
    
    @patch.object(FormatConverter, 'validate_params')
    @patch.object(FormatConverter, '_build_single_command')
    def test_execute_builds_command(self, mock_build_cmd, mock_validate):
        mock_build_cmd.return_value = ["ffmpeg", "-i", "test.mp4", "output.mp4"]
        
        with patch.object(self.converter._parser, 'get_media_info') as mock_get_info, \
             patch.object(self.converter._engine, 'build_command') as mock_engine_build, \
             patch.object(self.converter._engine, 'execute_sync') as mock_execute:
            
            mock_get_info.return_value = {
                "has_video": True,
                "has_audio": True,
                "duration": 100
            }
            mock_engine_build.return_value = ["ffmpeg", "-i", "test.mp4", "output.mp4"]
            mock_execute.return_value = {"success": True}
            
            params = self.converter.get_default_params()
            params["input_files"] = [str(self.temp_file)]
            params["output_dir"] = str(self.output_dir)
            self.converter.set_params(params)
            
            result = self.converter.execute()
            
            self.assertTrue(result)
    
    def test_set_and_get_params(self):
        params = {
            "input_files": ["test1.mp4", "test2.mp4"],
            "output_dir": "/test/output",
            "output_format": ".mkv"
        }
        
        self.converter.set_params(params)
        retrieved = self.converter.get_params()
        
        self.assertEqual(retrieved["input_files"], ["test1.mp4", "test2.mp4"])
        self.assertEqual(retrieved["output_dir"], "/test/output")
        self.assertEqual(retrieved["output_format"], ".mkv")
    
    def test_reset(self):
        custom_params = {
            "input_files": ["test.mp4"],
            "output_dir": "/test/output"
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
