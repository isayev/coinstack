"""
Backup Service - Full application state backup and restore functionality.

Creates versioned backups including:
- SQLite database
- Coin images
- Settings (.env)
- User uploads

Maintains 5 rolling backup versions with automatic rotation.
"""

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import get_settings


class BackupService:
    """Service for creating and managing application backups."""
    
    MAX_VERSIONS = 5
    
    def __init__(self):
        self.settings = get_settings()
        self.backend_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.backend_dir / "data"
        self.backups_dir = self.backend_dir / "backups"
        
        # Paths to backup
        self.database_path = Path(self.settings.DATABASE_URL.replace("sqlite:///", ""))
        if not self.database_path.is_absolute():
            self.database_path = self.backend_dir / self.database_path
        
        self.coin_images_dir = self.data_dir / "coin_images"
        self.cng_images_dir = self.data_dir / "cng_images"
        self.uploads_dir = self.backend_dir / "uploads"
        self.env_file = self.backend_dir / ".env"
    
    def get_backup_versions(self) -> list[str]:
        """Get list of available backup versions, sorted newest first."""
        if not self.backups_dir.exists():
            return []
        
        versions = []
        for item in self.backups_dir.iterdir():
            if item.is_dir() and self._is_valid_version(item.name):
                versions.append(item.name)
            elif item.suffix == ".zip" and self._is_valid_version(item.stem):
                versions.append(item.stem)
        
        return sorted(versions, reverse=True)
    
    def _is_valid_version(self, name: str) -> bool:
        """Check if name matches backup version format (YYYYMMDD_HHMMSS)."""
        if len(name) != 15 or name[8] != "_":
            return False
        try:
            datetime.strptime(name, "%Y%m%d_%H%M%S")
            return True
        except ValueError:
            return False
    
    def get_backup_manifest(self, version: str) -> Optional[dict]:
        """Get manifest for a specific backup version."""
        version_path = self.backups_dir / version
        zip_path = self.backups_dir / f"{version}.zip"
        
        if version_path.exists():
            manifest_path = version_path / "manifest.json"
            if manifest_path.exists():
                return json.loads(manifest_path.read_text(encoding="utf-8"))
        elif zip_path.exists():
            with zipfile.ZipFile(zip_path, "r") as zf:
                if "manifest.json" in zf.namelist():
                    return json.loads(zf.read("manifest.json").decode("utf-8"))
        
        return None
    
    def create_backup(self, compress: bool = True) -> dict:
        """
        Create a new backup of the application state.
        
        Args:
            compress: If True, creates a compressed ZIP archive.
            
        Returns:
            Dictionary with backup details including version and stats.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backups_dir / timestamp
        
        # Ensure backups directory exists
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        backup_path.mkdir(exist_ok=True)
        
        # Initialize manifest
        manifest = {
            "version": timestamp,
            "created_at": datetime.now().isoformat(),
            "compressed": compress,
            "components": {},
            "stats": {
                "total_files": 0,
                "total_size_bytes": 0,
            },
        }
        
        # 1. Backup Database
        if self.database_path.exists():
            db_backup = backup_path / "coinstack.db"
            shutil.copy2(self.database_path, db_backup)
            manifest["components"]["database"] = {
                "file": "coinstack.db",
                "size_bytes": db_backup.stat().st_size,
                "original_path": str(self.database_path),
            }
            manifest["stats"]["total_files"] += 1
            manifest["stats"]["total_size_bytes"] += db_backup.stat().st_size
        else:
            manifest["components"]["database"] = {"status": "not_found"}
        
        # 2. Backup Settings
        settings_dir = backup_path / "settings"
        settings_dir.mkdir(exist_ok=True)
        
        if self.env_file.exists():
            env_backup = settings_dir / ".env"
            shutil.copy2(self.env_file, env_backup)
            manifest["components"]["settings"] = {
                "file": "settings/.env",
                "size_bytes": env_backup.stat().st_size,
                "original_path": str(self.env_file),
            }
            manifest["stats"]["total_files"] += 1
        else:
            manifest["components"]["settings"] = {"status": "not_found"}
        
        # 3. Backup Images
        images_dir = backup_path / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Coin images
        if self.coin_images_dir.exists():
            coin_backup = images_dir / "coin_images"
            shutil.copytree(self.coin_images_dir, coin_backup)
            files = list(coin_backup.rglob("*"))
            file_count = len([f for f in files if f.is_file()])
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            manifest["components"]["coin_images"] = {
                "directory": "images/coin_images",
                "file_count": file_count,
                "size_bytes": total_size,
                "original_path": str(self.coin_images_dir),
            }
            manifest["stats"]["total_files"] += file_count
            manifest["stats"]["total_size_bytes"] += total_size
        else:
            manifest["components"]["coin_images"] = {"status": "not_found"}
        
        # CNG images
        if self.cng_images_dir.exists():
            cng_backup = images_dir / "cng_images"
            shutil.copytree(self.cng_images_dir, cng_backup)
            files = list(cng_backup.rglob("*"))
            file_count = len([f for f in files if f.is_file()])
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            manifest["components"]["cng_images"] = {
                "directory": "images/cng_images",
                "file_count": file_count,
                "size_bytes": total_size,
                "original_path": str(self.cng_images_dir),
            }
            manifest["stats"]["total_files"] += file_count
            manifest["stats"]["total_size_bytes"] += total_size
        else:
            manifest["components"]["cng_images"] = {"status": "not_found"}
        
        # 4. Backup Uploads
        if self.uploads_dir.exists():
            uploads_backup = backup_path / "uploads"
            shutil.copytree(self.uploads_dir, uploads_backup)
            files = list(uploads_backup.rglob("*"))
            file_count = len([f for f in files if f.is_file()])
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            manifest["components"]["uploads"] = {
                "directory": "uploads",
                "file_count": file_count,
                "size_bytes": total_size,
                "original_path": str(self.uploads_dir),
            }
            manifest["stats"]["total_files"] += file_count
            manifest["stats"]["total_size_bytes"] += total_size
        else:
            manifest["components"]["uploads"] = {"status": "not_found"}
        
        # Write manifest
        manifest_path = backup_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        
        # Compress if requested
        if compress:
            zip_path = self.backups_dir / f"{timestamp}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file in backup_path.rglob("*"):
                    if file.is_file():
                        arcname = file.relative_to(backup_path)
                        zf.write(file, arcname)
            
            # Remove uncompressed directory
            shutil.rmtree(backup_path)
            
            # Update manifest with compressed size
            manifest["compressed_size_bytes"] = zip_path.stat().st_size
        
        # Rotate old backups
        self._rotate_backups()
        
        return {
            "version": timestamp,
            "created_at": manifest["created_at"],
            "total_files": manifest["stats"]["total_files"],
            "total_size_mb": round(manifest["stats"]["total_size_bytes"] / (1024 * 1024), 2),
            "compressed": compress,
            "path": str(self.backups_dir / (f"{timestamp}.zip" if compress else timestamp)),
        }
    
    def _rotate_backups(self):
        """Remove old backups, keeping only MAX_VERSIONS most recent."""
        versions = self.get_backup_versions()
        
        if len(versions) > self.MAX_VERSIONS:
            to_remove = versions[self.MAX_VERSIONS:]
            
            for version in to_remove:
                version_path = self.backups_dir / version
                zip_path = self.backups_dir / f"{version}.zip"
                
                if version_path.exists():
                    shutil.rmtree(version_path)
                if zip_path.exists():
                    zip_path.unlink()
    
    def restore_backup(self, version: str) -> dict:
        """
        Restore application state from a backup version.
        
        Args:
            version: Backup version string (YYYYMMDD_HHMMSS).
            
        Returns:
            Dictionary with restore details.
            
        Raises:
            FileNotFoundError: If backup version doesn't exist.
            ValueError: If backup manifest is invalid.
        """
        version_path = self.backups_dir / version
        zip_path = self.backups_dir / f"{version}.zip"
        
        # Create pre-restore safety backup
        safety_backup = self.create_backup(compress=True)
        
        # Determine source (directory or zip)
        temp_extract_path = None
        if zip_path.exists():
            temp_extract_path = self.backups_dir / f"_temp_restore_{version}"
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(temp_extract_path)
            source_path = temp_extract_path
        elif version_path.exists():
            source_path = version_path
        else:
            raise FileNotFoundError(f"Backup version '{version}' not found")
        
        manifest_path = source_path / "manifest.json"
        if not manifest_path.exists():
            if temp_extract_path:
                shutil.rmtree(temp_extract_path)
            raise ValueError(f"Invalid backup: manifest.json not found")
        
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        restored = []
        
        try:
            # Restore Database
            if manifest["components"].get("database", {}).get("file"):
                db_source = source_path / "coinstack.db"
                if db_source.exists():
                    self.database_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(db_source, self.database_path)
                    restored.append("database")
            
            # Restore Settings
            if manifest["components"].get("settings", {}).get("file"):
                env_source = source_path / "settings" / ".env"
                if env_source.exists():
                    shutil.copy2(env_source, self.env_file)
                    restored.append("settings")
            
            # Restore Coin Images
            if manifest["components"].get("coin_images", {}).get("directory"):
                img_source = source_path / "images" / "coin_images"
                if img_source.exists():
                    if self.coin_images_dir.exists():
                        shutil.rmtree(self.coin_images_dir)
                    shutil.copytree(img_source, self.coin_images_dir)
                    restored.append("coin_images")
            
            # Restore CNG Images
            if manifest["components"].get("cng_images", {}).get("directory"):
                cng_source = source_path / "images" / "cng_images"
                if cng_source.exists():
                    if self.cng_images_dir.exists():
                        shutil.rmtree(self.cng_images_dir)
                    shutil.copytree(cng_source, self.cng_images_dir)
                    restored.append("cng_images")
            
            # Restore Uploads
            if manifest["components"].get("uploads", {}).get("directory"):
                uploads_source = source_path / "uploads"
                if uploads_source.exists():
                    if self.uploads_dir.exists():
                        shutil.rmtree(self.uploads_dir)
                    shutil.copytree(uploads_source, self.uploads_dir)
                    restored.append("uploads")
                    
        finally:
            # Clean up temp extraction
            if temp_extract_path and temp_extract_path.exists():
                shutil.rmtree(temp_extract_path)
        
        return {
            "restored_version": version,
            "restored_components": restored,
            "safety_backup_version": safety_backup["version"],
            "message": "Restore completed. Please restart the application.",
        }
    
    def list_backups(self) -> list[dict]:
        """Get detailed information about all available backups."""
        backups = []
        
        for version in self.get_backup_versions():
            manifest = self.get_backup_manifest(version)
            
            zip_path = self.backups_dir / f"{version}.zip"
            version_path = self.backups_dir / version
            
            if manifest:
                size_bytes = manifest["stats"]["total_size_bytes"]
                compressed_size = manifest.get("compressed_size_bytes")
                
                if not compressed_size and zip_path.exists():
                    compressed_size = zip_path.stat().st_size
                
                backups.append({
                    "version": version,
                    "created_at": manifest["created_at"],
                    "total_files": manifest["stats"]["total_files"],
                    "size_mb": round(size_bytes / (1024 * 1024), 2),
                    "compressed_size_mb": round(compressed_size / (1024 * 1024), 2) if compressed_size else None,
                    "compressed": manifest.get("compressed", zip_path.exists()),
                    "components": list(
                        k for k, v in manifest["components"].items() 
                        if v.get("status") != "not_found"
                    ),
                })
            else:
                # Backup exists but manifest is missing/corrupted
                backups.append({
                    "version": version,
                    "created_at": None,
                    "error": "Manifest not found or corrupted",
                    "compressed": zip_path.exists(),
                })
        
        return backups


# Singleton instance
_backup_service: Optional[BackupService] = None


def get_backup_service() -> BackupService:
    """Get or create backup service instance."""
    global _backup_service
    if _backup_service is None:
        _backup_service = BackupService()
    return _backup_service
