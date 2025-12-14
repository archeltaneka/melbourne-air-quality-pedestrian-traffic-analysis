from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import patch, Mock

from src.downloader import Downloader


@pytest.fixture
def downloader(tmp_path):
    """Fixture to create a Downloader instance with temporary directory"""
    with patch.object(Downloader, '__init__', lambda self: None):
        dl = Downloader()
        dl.data_dir = tmp_path / 'data'
        dl.air_quality_dir = dl.data_dir / 'air_quality'
        dl.pedestrian_dir = dl.data_dir / 'pedestrian'
        dl.logger = Mock()
        
        return dl


@pytest.fixture
def mock_urlretrieve():
    """Fixture to mock urllib.request.urlretrieve"""
    with patch('urllib.request.urlretrieve') as mock:
        yield mock