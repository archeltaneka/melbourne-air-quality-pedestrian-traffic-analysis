from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import patch
import urllib

from src.downloader import Downloader


class TestDownloader:

    # Test __init__ method
    def test_init_creates_correct_paths(self):
        """Test that __init__ sets up correct directory paths"""
        dl = Downloader()
        assert dl.data_dir == Path('data')
        assert dl.air_quality_dir == Path('data/air_quality')
        assert dl.pedestrian_dir == Path('data/pedestrian')
        assert dl.air_quality_web_dir == Path('web/data/air_quality')
        assert dl.pedestrian_web_dir == Path('web/data/pedestrian')
        assert dl.logger is not None


    def test_logger_configured_correctly(self):
        """Test that logger is configured on initialization"""
        dl = Downloader()
        assert dl.logger.name == 'src.downloader'


    # Test _setup method
    def test_setup_creates_directories(self, downloader, tmp_path):
        """Test that _setup creates all required directories"""
        downloader._setup()
        
        assert downloader.data_dir.exists()
        assert downloader.air_quality_dir.exists()
        assert downloader.pedestrian_dir.exists()
        assert downloader.air_quality_web_dir.exists()
        assert downloader.pedestrian_web_dir.exists()
        downloader.logger.info.assert_called_with('Setting up data directory...')


    # Test _setup method when directories already exist
    def test_setup_handles_existing_directories(self, downloader, tmp_path):
        """Test that _setup doesn't fail if directories already exist"""
        # Create directories first
        downloader.data_dir.mkdir(parents=True, exist_ok=True)
        downloader.air_quality_dir.mkdir(parents=True, exist_ok=True)
        downloader.pedestrian_dir.mkdir(parents=True, exist_ok=True)
        downloader.air_quality_web_dir.mkdir(parents=True, exist_ok=True)
        downloader.pedestrian_web_dir.mkdir(parents=True, exist_ok=True)
        
        # Should not raise any exception
        downloader._setup()
        
        assert downloader.data_dir.exists()
        assert downloader.air_quality_dir.exists()
        assert downloader.pedestrian_dir.exists()
        assert downloader.air_quality_web_dir.exists()
        assert downloader.pedestrian_web_dir.exists()


    # Test _setup method when parent directory doesn't exist
    def test_setup_creates_nested_directories(self, downloader, tmp_path):
        """Test that _setup creates nested directory structure"""
        # Ensure parent doesn't exist
        assert not downloader.data_dir.exists()
        
        downloader._setup()
        
        # All nested directories should be created
        assert downloader.data_dir.exists()
        assert downloader.air_quality_dir.exists()
        assert downloader.pedestrian_dir.exists()
        assert downloader.air_quality_web_dir.exists()
        assert downloader.pedestrian_web_dir.exists()

    
    # Test _download method
    def test_download_success(self, downloader, mock_urlretrieve, tmp_path):
        """Test successful file download"""
        url = "https://example.com/file.csv"
        save_path = tmp_path / "test_file.csv"
        
        downloader._download(url, save_path)
        
        mock_urlretrieve.assert_called_once_with(url, save_path)
        downloader.logger.info.assert_any_call(f"Downloading {url} to {save_path}...")
        downloader.logger.info.assert_any_call(f"Downloaded {url} to {save_path}")

    
    # Test _download method when network error occurs
    def test_download_handles_network_error(self, downloader, mock_urlretrieve, tmp_path):
        """Test that _download handles network errors gracefully"""
        url = "https://example.com/file.csv"
        save_path = tmp_path / "test_file.csv"
        
        mock_urlretrieve.side_effect = urllib.error.URLError("Network error")
        
        # Should not raise exception
        downloader._download(url, save_path)
        
        downloader.logger.error.assert_called_once()
        assert "Failed to download" in downloader.logger.error.call_args[0][0]

    
    def test_download_handles_http_error(self, downloader, mock_urlretrieve, tmp_path):
        """Test that _download handles HTTP errors (404, 500, etc.)"""
        url = "https://example.com/nonexistent.csv"
        save_path = tmp_path / "test_file.csv"
        
        mock_urlretrieve.side_effect = urllib.error.HTTPError(
            url, 404, "Not Found", {}, None
        )
        
        downloader._download(url, save_path)
        
        downloader.logger.error.assert_called_once()
        assert "Failed to download" in downloader.logger.error.call_args[0][0]


    def test_download_handles_permission_error(self, downloader, mock_urlretrieve, tmp_path):
        """Test that _download handles permission errors"""
        url = "https://example.com/file.csv"
        save_path = tmp_path / "test_file.csv"
        
        mock_urlretrieve.side_effect = PermissionError("Permission denied")
        
        downloader._download(url, save_path)
        
        downloader.logger.error.assert_called_once()
        assert "Failed to download" in downloader.logger.error.call_args[0][0]


    def test_download_handles_timeout(self, downloader, mock_urlretrieve, tmp_path):
        """Test that _download handles timeout errors"""
        url = "https://example.com/file.csv"
        save_path = tmp_path / "test_file.csv"
        
        mock_urlretrieve.side_effect = TimeoutError("Request timed out")
        
        downloader._download(url, save_path)
        
        downloader.logger.error.assert_called_once()


    def test_download_with_invalid_path(self, downloader, mock_urlretrieve):
        """Test _download with invalid file path"""
        url = "https://example.com/file.csv"
        save_path = Path("/invalid/path/file.csv")
        
        mock_urlretrieve.side_effect = OSError("Invalid path")
        
        downloader._download(url, save_path)
        
        downloader.logger.error.assert_called_once()


    # Test download method (main workflow)
    def test_download_calls_setup(self, downloader, mock_urlretrieve):
        """Test that download() calls _setup first"""
        with patch.object(downloader, '_setup') as mock_setup:
            downloader.download()
            mock_setup.assert_called_once()


    def test_download_downloads_air_quality(self, downloader, mock_urlretrieve):
        """Test that download() downloads air quality file"""
        downloader.download()
        
        # Check that air quality URL was called
        calls = mock_urlretrieve.call_args_list
        air_quality_call = calls[0]
        
        assert "apps.epa.vic.gov.au" in air_quality_call[0][0]
        assert "air_quality" in str(air_quality_call[0][1])


    def test_download_downloads_all_data(self, downloader, mock_urlretrieve):
        """Test that download() downloads all 12 months of pedestrian and air quality data"""
        downloader.download()
        
        # Should be called 13 times: 1 air quality + 12 pedestrian files
        assert mock_urlretrieve.call_count == 13


    def test_download_uses_correct_month_names(self, downloader, mock_urlretrieve):
        """Test that download() uses correct month names in URLs"""
        downloader.download()
        
        months = ['January', 'February', 'March', 'April', 'May', 'June', 
                  'July', 'August', 'September', 'October', 'November', 'December']
        
        calls = [str(call[0][0]) for call in mock_urlretrieve.call_args_list]
        
        for month in months:
            assert any(month in call for call in calls)


    def test_download_saves_to_correct_directories(self, downloader, mock_urlretrieve):
        """Test that download() saves files to correct directories"""
        downloader.download()
        
        calls = mock_urlretrieve.call_args_list
        
        # First call should be air quality (to air_quality_dir)
        assert 'air_quality' in str(calls[0][0][1])
        
        # Remaining calls should be pedestrian (to pedestrian_dir)
        for call in calls[1:]:
            assert 'pedestrian' in str(call[0][1])


    def test_download_logs_completion(self, downloader, mock_urlretrieve):
        """Test that download() logs completion message"""
        downloader.download()
        
        # Check that completion message was logged
        log_messages = [call[0][0] for call in downloader.logger.info.call_args_list]
        assert any("Download completed" in msg for msg in log_messages)

    
    def test_download_continues_on_single_failure(self, downloader, mock_urlretrieve):
        """Test that download() continues downloading even if one file fails"""
        # Make the 3rd download fail (first pedestrian file)
        mock_urlretrieve.side_effect = [
            None,  # Air quality succeeds
            None,  # January succeeds
            urllib.error.URLError("Network error"),  # February fails
            None, None, None, None, None, None, None, None, None, None  # Rest succeed
        ]
        
        downloader.download()
        
        # Should still attempt all 13 downloads
        assert mock_urlretrieve.call_count == 13
        
        # Should log at least one error
        assert downloader.logger.error.call_count >= 1


    def test_download_with_pathlib_path(self, downloader, mock_urlretrieve, tmp_path):
        """Test that download works with Path objects"""
        downloader.data_dir = tmp_path / 'data'
        downloader.air_quality_dir = downloader.data_dir / 'air_quality'
        downloader.pedestrian_dir = downloader.data_dir / 'pedestrian'
        downloader.air_quality_web_dir = downloader.web_dir / 'data' / 'air_quality'
        downloader.pedestrian_web_dir = downloader.web_dir / 'data' / 'pedestrian'
        
        # Should not raise any exceptions
        downloader.download()
        
        assert mock_urlretrieve.call_count == 13


    def test_download_with_empty_url(self, downloader, mock_urlretrieve):
        """Test _download with empty URL"""
        downloader._download("", Path("test.csv"))
        
        # Should attempt to download and log error if it fails
        mock_urlretrieve.assert_called_once()


    def test_download_with_special_characters_in_path(self, downloader, mock_urlretrieve, tmp_path):
        """Test _download with special characters in file path"""
        url = "https://example.com/file.csv"
        save_path = tmp_path / "test file with spaces.csv"
        
        downloader._download(url, save_path)
        
        mock_urlretrieve.assert_called_once_with(url, save_path)


    def test_multiple_download_calls(self, downloader, mock_urlretrieve):
        """Test calling download() multiple times"""
        downloader.download()
        downloader.download()
        
        # Should download all files twice
        assert mock_urlretrieve.call_count == 26  # 13 * 2
