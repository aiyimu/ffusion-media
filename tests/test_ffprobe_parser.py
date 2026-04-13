import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.core.ffprobe_parser import FFprobeParser
from src.core.exceptions import (
    FFprobeNotFoundError,
    FileNotFoundError,
    FileNotReadableError
)


class TestFFprobeParser(unittest.TestCase):
    
    def setUp(self):
        self.parser = FFprobeParser()
    
    def test_singleton_instance(self):
        parser1 = FFprobeParser()
        parser2 = FFprobeParser()
        self.assertIs(parser1, parser2)
    
    @patch('src.core.ffprobe_parser.get_ffprobe_path')
    def test_locate_ffprobe_success(self, mock_get_path):
        mock_path = Path("/fake/path/ffprobe")
        mock_get_path.return_value = mock_path
        parser = FFprobeParser()
        self.assertEqual(parser.get_ffprobe_path(), mock_path)
    
    @patch('src.core.ffprobe_parser.get_ffprobe_path')
    def test_locate_ffprobe_not_found(self, mock_get_path):
        mock_get_path.return_value = None
        parser = FFprobeParser()
        self.assertIsNone(parser.get_ffprobe_path())
    
    def test_set_ffprobe_path_invalid(self):
        with self.assertRaises(FFprobeNotFoundError):
            self.parser.set_ffprobe_path("/invalid/path/ffprobe")
    
    def test_validate_input_file_not_exists(self):
        with self.assertRaises(FileNotFoundError):
            self.parser._validate_input_file("/nonexistent/file.mp4")
    
    @patch('src.core.ffprobe_parser.FFprobeParser._execute_ffprobe')
    def test_get_media_info_success(self, mock_execute):
        mock_data = {
            "format": {
                "size": "1024000",
                "duration": "60.5",
                "bit_rate": "128000",
                "format_name": "mp4",
                "format_long_name": "MP4 (MPEG-4 Part 14)"
            },
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                    "pix_fmt": "yuv420p"
                },
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": 44100,
                    "channels": 2
                }
            ]
        }
        mock_execute.return_value = mock_data
        
        with patch.object(self.parser, '_validate_input_file'):
            with patch.object(self.parser, '_check_ffprobe_available'):
                info = self.parser.get_media_info("/fake/file.mp4")
                
                self.assertEqual(info["file_size"], 1024000)
                self.assertEqual(info["duration"], 60.5)
                self.assertTrue(info["has_video"])
                self.assertTrue(info["has_audio"])
                self.assertEqual(info["video"]["width"], 1920)
                self.assertEqual(info["video"]["height"], 1080)
                self.assertEqual(info["audio"]["channels"], 2)
    
    def test_parse_frame_rate(self):
        self.assertEqual(self.parser._parse_frame_rate("30/1"), 30.0)
        self.assertEqual(self.parser._parse_frame_rate("60/1"), 60.0)
        self.assertEqual(self.parser._parse_frame_rate("30000/1001"), 29.97002997002997)
        self.assertEqual(self.parser._parse_frame_rate("0/1"), 0.0)
        self.assertEqual(self.parser._parse_frame_rate("invalid"), 0.0)
    
    @patch('src.core.ffprobe_parser.FFprobeParser.get_media_info')
    def test_is_valid_media_file_true(self, mock_get_info):
        mock_get_info.return_value = {"has_video": True, "has_audio": False}
        self.assertTrue(self.parser.is_valid_media_file("/fake/file.mp4"))
    
    @patch('src.core.ffprobe_parser.FFprobeParser.get_media_info')
    def test_is_valid_media_file_false(self, mock_get_info):
        mock_get_info.side_effect = Exception("Invalid file")
        self.assertFalse(self.parser.is_valid_media_file("/fake/file.txt"))


if __name__ == "__main__":
    unittest.main()
