"""Data loading and downloading utilities."""

import os
import requests
import logging
import gzip
from typing import Optional

from ..config.settings import DatabaseConfig


class DataLoader:
    """Handle downloading and validation of movie dataset."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def download_dataset(self, force_download: bool = False) -> bool:
        """Download the MSRD dataset from GitHub."""
        if os.path.exists(self.config.movies_path) and not force_download:
            self.logger.info("Dataset already exists. Use force_download=True to re-download.")
            return True

        os.makedirs(self.config.data_dir, exist_ok=True)

        # MSRD GitHub repository URL
        url = "https://github.com/metarank/msrd/raw/master/dataset/movies.csv.gz"

        try:
            self.logger.info(f"Downloading dataset from {url}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Download compressed file
            compressed_path = os.path.join(self.config.data_dir, "movies.csv.gz")
            with open(compressed_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Decompress and rename
            with gzip.open(compressed_path, 'rt', encoding='utf-8') as f_in:
                with open(self.config.movies_path, 'w', encoding='utf-8') as f_out:
                    f_out.write(f_in.read())

            # Clean up compressed file
            os.remove(compressed_path)
            
            self.logger.info(f"Dataset downloaded successfully to {self.config.movies_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download dataset: {e}")
            return False
    
    def verify_dataset(self) -> bool:
        """Verify that the dataset exists and has basic structure."""
        if not os.path.exists(self.config.movies_path):
            self.logger.error(f"Dataset file not found: {self.config.movies_path}")
            return False
        
        try:
            # Check file size (should be > 1MB for MSRD dataset)
            file_size = os.path.getsize(self.config.movies_path)
            if file_size < 1024 * 1024:  # 1MB
                self.logger.error(f"Dataset file too small: {file_size} bytes")
                return False
            
            self.logger.info(f"Dataset verified: {file_size / (1024*1024):.2f} MB")
            return True
            
        except Exception as e:
            self.logger.error(f"Dataset verification failed: {e}")
            return False
    
    def ensure_dataset_available(self) -> bool:
        """Ensure dataset is available, download if necessary."""
        if self.verify_dataset():
            return True
        
        self.logger.info("Dataset not available, attempting to download...")
        return self.download_dataset()
