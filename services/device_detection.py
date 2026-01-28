"""
Device detection service for KOReader devices
"""

import os
import platform
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


class DeviceDetection:
    """Service for detecting KOReader devices"""
    
    def __init__(self):
        self.system = platform.system()
        logger.info(f"Initializing device detection for {self.system}")
    
    def get_koreader_paths(self) -> List[str]:
        """
        Get possible KOReader installation paths based on the operating system.
        Enhanced version that looks for folders named 'koreader'.
        
        Returns:
            List of possible KOReader paths
        """
        paths = []
        
        if self.system == "Windows":
            # Check common removable drive letters
            for drive in ["E:", "F:", "G:", "H:", "I:", "J:", "K:", "L:", "M:", "N:", "O:", "P:", "Q:", "R:", "S:", "T:", "U:", "V:", "W:", "X:", "Y:", "Z:"]:
                if os.path.exists(drive):
                    # Look for folders named 'koreader' in common locations
                    search_locations = [
                        ".adds",
                        "extensions", 
                        "documents",
                        ".kobo",
                        "applications",
                        ""  # root of drive
                    ]
                    
                    for location in search_locations:
                        search_path = os.path.join(drive, location) if location else drive
                        if os.path.exists(search_path):
                            # Look for 'koreader' folder
                            koreader_folder = os.path.join(search_path, "koreader")
                            if os.path.exists(koreader_folder) and self._has_koreader(koreader_folder):
                                paths.append(koreader_folder)
            
            # Check local installations
            local_paths = [
                os.path.expanduser("~/koreader"),
                "C:/koreader",
                "C:/Program Files/koreader",
                "C:/Program Files (x86)/koreader"
            ]
            
            for path in local_paths:
                if os.path.exists(path) and self._has_koreader(path):
                    paths.append(path)
        
        elif self.system == "Darwin":  # macOS
            mac_paths = [
                "/Volumes/koreader",
                "/Volumes/KOReader",
                os.path.expanduser("~/koreader"),
                "/Applications/koreader"
            ]
            
            for path in mac_paths:
                if os.path.exists(path) and self._has_koreader(path):
                    paths.append(path)
        
        elif self.system == "Linux":
            linux_paths = [
                "/media/*/koreader",
                "/mnt/*/koreader",
                os.path.expanduser("~/koreader"),
                "/opt/koreader"
            ]
            
            for path in linux_paths:
                # Handle wildcards for Linux
                if "*" in path:
                    import glob
                    found_paths = glob.glob(path)
                    for found_path in found_paths:
                        if self._has_koreader(found_path):
                            paths.append(found_path)
                elif os.path.exists(path) and self._has_koreader(path):
                    paths.append(path)
        
        logger.info(f"Found KOReader paths: {paths}")
        return paths
    
    def _has_koreader(self, path: str) -> bool:
        """Detects KOReader by looking for koreader.sh first, then settings.reader.lua"""
        # First check for koreader.sh
        if os.path.exists(os.path.join(path, "koreader.sh")):
            return True
        
        # Then check for settings.reader.lua (present on all devices)
        if os.path.exists(os.path.join(path, "settings.reader.lua")):
            return True
        
        return False
    
    def validate_koreader_installation(self, path: str) -> bool:
        """
        Validate if the given path is a valid KOReader installation.
        
        Args:
            path: Path to check
            
        Returns:
            True if valid KOReader installation, False otherwise
        """
        if not os.path.exists(path):
            return False
        
        # Check for essential KOReader files/directories
        essential_items = [
            "koreader.sh",
            "frontend",
            "plugins",
            "data"
        ]
        
        for item in essential_items:
            item_path = os.path.join(path, item)
            if not os.path.exists(item_path):
                logger.debug(f"Missing essential item {item} in {path}")
                return False
        
        logger.info(f"Validated KOReader installation at {path}")
        return True
    
    def detect_koreader_device(self) -> Optional[str]:
        """
        Automatically detect KOReader device.
        If multiple devices are found, prompts user to select one.
        This detection is not cached.
        
        Returns:
            Path to KOReader installation if found, None otherwise
        """
        logger.info("Starting automatic KOReader device detection")
        
        possible_paths = self.get_koreader_paths()
        
        if not possible_paths:
            logger.warning("No KOReader device detected")
            return None
        
        # If only one path found, use it
        if len(possible_paths) == 1:
            selected_path = possible_paths[0]
            logger.info(f"Detected single KOReader device at: {selected_path}")
            return selected_path
        
        # Multiple paths found - return list for UI to handle selection
        logger.info(f"Multiple KOReader devices found: {possible_paths}")
        return possible_paths
    
    def get_device_info(self, koreader_path: str) -> dict:
        """
        Get information about the KOReader device.
        
        Args:
            koreader_path: Path to KOReader installation
            
        Returns:
            Dictionary with device information
        """
        info = {
            "path": koreader_path,
            "valid": False,
            "version": "Unknown",
            "platform": self.system
        }
        
        if self.validate_koreader_installation(koreader_path):
            info["valid"] = True
            
            # Try to read version info
            version_file = os.path.join(koreader_path, "git-rev")
            if os.path.exists(version_file):
                try:
                    with open(version_file, 'r') as f:
                        info["version"] = f.read().strip()
                except Exception as e:
                    logger.warning(f"Could not read version file: {e}")
            
            # Check for plugins directory
            plugins_dir = os.path.join(koreader_path, "plugins")
            info["plugins_exist"] = os.path.exists(plugins_dir)
            
            # Check for patches directory
            patches_dir = os.path.join(koreader_path, "patches")
            info["patches_exist"] = os.path.exists(patches_dir)
        
        return info
