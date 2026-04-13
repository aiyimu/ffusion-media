import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.modules.audio_processor import AudioProcessor
from src.core.exceptions import (
    MissingParameterError,
    InvalidParameterError,
    FileNotFoundError,
    FileNotReadableError
)


class TestAudioProcessor(unittest.TestCase):
    
    def setUp(self):
        self.processor = AudioProcessor()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.temp_file = self.temp_dir / "test.mp4"
        self.temp_file.touch()
        self.output_dir = self.temp_dir / "output"
        self.output_dir.mkdir()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_default_params(self):
        params = self.processor.get_default_params()
        
        self.assertIn("input_files", params)
        self.assertIn("output_dir", params)
        self.assertIn("output_format", params)
        self.assertIn("process_mode", params)
        self.assertIn("volume_percent", params)
        self.assertIn("channel_mode", params)
        self.assertIn("denoise_strength", params)
        self.assertIn("start_time", params)
        self.assertIn("end_time", params)
        self.assertIn("overwrite", params)
        self.assertIn("output_suffix", params)
        
        self.assertEqual(params["process_mode"], "extract")
        self.assertEqual(params["output_format"], ".mp3")
        self.assertEqual(params["volume_percent"], 100)
    
    def test_validate_params_missing_input_files(self):
        params = self.processor.get_default_params()
        params["input_files"] = []
        params["output_dir"] = str(self.output_dir)
        self.processor.set_params(params)
        
        with self.assertRaises(MissingParameterError):
            self.processor.validate_params()
    
    def test_validate_params_missing_output_dir(self):
        params = self.processor.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = ""
        self.processor.set_params(params)
        
        with self.assertRaises(MissingParameterError):
            self.processor.validate_params()
    
    def test_validate_params_nonexistent_file(self):
        params = self.processor.get_default_params()
        params["input_files"] = ["nonexistent.mp4"]
        params["output_dir"] = str(self.output_dir)
        self.processor.set_params(params)
        
        with self.assertRaises(FileNotFoundError):
            self.processor.validate_params()
    
    def test_validate_params_invalid_output_format(self):
        params = self.processor.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["output_format"] = ".xyz"
        self.processor.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.processor.validate_params()
    
    def test_validate_params_invalid_process_mode(self):
        params = self.processor.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "invalid_mode"
        self.processor.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.processor.validate_params()
    
    def test_validate_params_volume_out_of_range(self):
        params = self.processor.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "volume"
        params["volume_percent"] = 250
        self.processor.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.processor.validate_params()
    
    def test_validate_params_volume_zero(self):
        params = self.processor.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "volume"
        params["volume_percent"] = -10
        self.processor.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.processor.validate_params()
    
    def test_validate_params_invalid_channel_mode(self):
        params = self.processor.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "channel"
        params["channel_mode"] = "invalid_mode"
        self.processor.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.processor.validate_params()
    
    def test_validate_params_denoise_out_of_range(self):
        params = self.processor.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "denoise"
        params["denoise_strength"] = 2.0
        self.processor.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.processor.validate_params()
    
    def test_validate_params_cut_time_invalid_order(self):
        params = self.processor.get_default_params()
        params["input_files"] = [str(self.temp_file)]
        params["output_dir"] = str(self.output_dir)
        params["process_mode"] = "cut"
        params["start_time"] = "0:00:20"
        params["end_time"] = "0:00:10"
        self.processor.set_params(params)
        
        with self.assertRaises(InvalidParameterError):
            self.processor.validate_params()
    
    def test_get_supported_input_formats(self):
        formats = self.processor.get_supported_input_formats()
        self.assertIsInstance(formats, list)
        self.assertGreater(len(formats), 0)
    
    def test_get_supported_output_formats(self):
        formats = self.processor.get_supported_output_formats()
        self.assertIsInstance(formats, list)
        self.assertIn(".mp3", formats)
        self.assertIn(".wav", formats)
        self.assertIn(".flac", formats)
        self.assertIn(".aac", formats)
    
    def test_get_default_audio_codec(self):
        self.assertEqual(self.processor._get_default_audio_codec(".mp3"), "libmp3lame")
        self.assertEqual(self.processor._get_default_audio_codec(".wav"), "pcm_s16le")
        self.assertEqual(self.processor._get_default_audio_codec(".flac"), "flac")
        self.assertEqual(self.processor._get_default_audio_codec(".aac"), "aac")
        self.assertEqual(self.processor._get_default_audio_codec(".unknown"), "aac")
    
    def test_build_single_command_extract(self):
        with patch.object(self.processor._parser, 'get_media_info') as mock_get_info:
            mock_get_info.return_value = {
                "has_video": True,
                "has_audio": True,
                "duration": 100
            }
            
            input_path = Path("/test/input.mp4")
            output_path = Path("/test/output.mp3")
            media_info = {"has_video": True, "has_audio": True, "duration": 100}
            
            self.processor.set_params({
                "process_mode": "extract",
                "output_format": ".mp3"
            })
            
            command = self.processor._build_single_command(input_path, output_path, media_info)
            
            self.assertIn("-i", command)
            self.assertIn("-vn", command)
            self.assertIn("-c:a", command)
            self.assertIn("libmp3lame", command)
    
    def test_build_single_command_volume(self):
        with patch.object(self.processor._parser, 'get_media_info') as mock_get_info:
            mock_get_info.return_value = {
                "has_video": True,
                "has_audio": True,
                "duration": 100
            }
            
            input_path = Path("/test/input.mp3")
            output_path = Path("/test/output.mp3")
            media_info = {"has_video": False, "has_audio": True, "duration": 100}
            
            self.processor.set_params({
                "process_mode": "volume",
                "volume_percent": 150,
                "output_format": ".mp3"
            })
            
            command = self.processor._build_single_command(input_path, output_path, media_info)
            
            self.assertIn("-i", command)
            self.assertIn("-vn", command)
            self.assertIn("-filter:a", command)
            self.assertIn("volume=1.5", command)
    
    def test_build_single_command_channel_mono(self):
        with patch.object(self.processor._parser, 'get_media_info') as mock_get_info:
            mock_get_info.return_value = {
                "has_video": False,
                "has_audio": True,
                "duration": 100
            }
            
            input_path = Path("/test/input.mp3")
            output_path = Path("/test/output.mp3")
            media_info = {"has_video": False, "has_audio": True, "duration": 100}
            
            self.processor.set_params({
                "process_mode": "channel",
                "channel_mode": "mono",
                "output_format": ".mp3"
            })
            
            command = self.processor._build_single_command(input_path, output_path, media_info)
            
            self.assertIn("-i", command)
            self.assertIn("-vn", command)
            self.assertIn("-ac", command)
            self.assertIn("1", command)
    
    def test_build_single_command_cut(self):
        with patch.object(self.processor._parser, 'get_media_info') as mock_get_info:
            mock_get_info.return_value = {
                "has_video": False,
                "has_audio": True,
                "duration": 100
            }
            
            input_path = Path("/test/input.mp3")
            output_path = Path("/test/output.mp3")
            media_info = {"has_video": False, "has_audio": True, "duration": 100}
            
            self.processor.set_params({
                "process_mode": "cut",
                "start_time": "0:00:05",
                "end_time": "0:00:15",
                "output_format": ".mp3"
            })
            
            command = self.processor._build_single_command(input_path, output_path, media_info)
            
            self.assertIn("-i", command)
            self.assertIn("-vn", command)
            self.assertIn("-ss", command)
            self.assertIn("0:00:05", command)
            self.assertIn("-t", command)
            self.assertIn("10.0", command)
            self.assertIn("-c:a", command)
            self.assertIn("copy", command)
    
    @patch.object(AudioProcessor, 'validate_params')
    @patch.object(AudioProcessor, '_build_single_command')
    @patch.object(AudioProcessor, '_validate_audio_available')
    def test_execute_builds_command(self, mock_validate_audio, mock_build_cmd, mock_validate):
        mock_build_cmd.return_value = ["ffmpeg", "-i", "test.mp4", "output.mp3"]
        
        with patch.object(self.processor._parser, 'get_media_info') as mock_get_info, \
             patch.object(self.processor._engine, 'build_command') as mock_engine_build, \
             patch.object(self.processor._engine, 'execute_sync') as mock_execute:
            
            mock_get_info.return_value = {
                "has_video": True,
                "has_audio": True,
                "duration": 100
            }
            mock_engine_build.return_value = ["ffmpeg", "-i", "test.mp4", "output.mp3"]
            mock_execute.return_value = {"success": True}
            
            params = self.processor.get_default_params()
            params["input_files"] = [str(self.temp_file)]
            params["output_dir"] = str(self.output_dir)
            self.processor.set_params(params)
            
            result = self.processor.execute()
            
            self.assertTrue(result)
    
    def test_set_and_get_params(self):
        params = {
            "input_files": ["audio1.mp3", "audio2.wav"],
            "output_dir": "/test/output",
            "output_format": ".flac",
            "process_mode": "volume",
            "volume_percent": 80
        }
        
        self.processor.set_params(params)
        retrieved = self.processor.get_params()
        
        self.assertEqual(retrieved["input_files"], ["audio1.mp3", "audio2.wav"])
        self.assertEqual(retrieved["output_dir"], "/test/output")
        self.assertEqual(retrieved["output_format"], ".flac")
        self.assertEqual(retrieved["process_mode"], "volume")
        self.assertEqual(retrieved["volume_percent"], 80)
    
    def test_reset(self):
        custom_params = {
            "input_files": ["audio.mp3"],
            "output_dir": "/test/output",
            "process_mode": "denoise"
        }
        
        self.processor.set_params(custom_params)
        self.processor.reset()
        
        default_params = self.processor.get_default_params()
        current_params = self.processor.get_params()
        
        self.assertEqual(current_params, default_params)
        self.assertFalse(self.processor.is_running())
        self.assertFalse(self.processor.is_cancelled())
    
    def test_cancel(self):
        self.assertFalse(self.processor.is_cancelled())
        self.processor.cancel()
        self.assertTrue(self.processor.is_cancelled())
        self.processor.reset()
        self.assertFalse(self.processor.is_cancelled())


if __name__ == '__main__':
    unittest.main()
