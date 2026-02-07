import json
import os
from typing import List, Dict, Any, Optional
from app.config import USERS_FILE, DETECTIONS_FILE, DATA_DIR

class JSONHandler:
    """Handle JSON file operations for storage"""
    
    @staticmethod
    def read_json(filepath: str) -> Dict[str, Any]:
        """Read JSON file, return empty dict if not exists"""
        if not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    @staticmethod
    def write_json(filepath: str, data: Dict[str, Any]) -> bool:
        """Write data to JSON file"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error writing to {filepath}: {e}")
            return False
    
    @staticmethod
    def append_to_json(filepath: str, key: str, value: Any) -> bool:
        """Append value to JSON array at key"""
        try:
            data = JSONHandler.read_json(filepath)
            if key not in data:
                data[key] = []
            data[key].append(value)
            return JSONHandler.write_json(filepath, data)
        except Exception as e:
            print(f"Error appending to {filepath}: {e}")
            return False
    
    @staticmethod
    def update_in_json(filepath: str, key: str, value: Any) -> bool:
        """Update or create key in JSON"""
        try:
            data = JSONHandler.read_json(filepath)
            data[key] = value
            return JSONHandler.write_json(filepath, data)
        except Exception as e:
            print(f"Error updating {filepath}: {e}")
            return False

class UserStorage:
    """Handle user data storage"""
    
    @staticmethod
    def get_all_users() -> Dict[str, Dict[str, Any]]:
        """Get all users from storage"""
        data = JSONHandler.read_json(USERS_FILE)
        return data.get('users', {})
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        users = UserStorage.get_all_users()
        return users.get(email)
    
    @staticmethod
    def create_user(email: str, name: str, hashed_password: str) -> bool:
        """Create new user"""
        data = JSONHandler.read_json(USERS_FILE)
        if 'users' not in data:
            data['users'] = {}
        
        if email in data['users']:
            return False
        
        data['users'][email] = {
            'email': email,
            'name': name,
            'password': hashed_password,
            'created_at': str(os.popen('date /t').read().strip())
        }
        return JSONHandler.write_json(USERS_FILE, data)
    
    @staticmethod
    def user_exists(email: str) -> bool:
        """Check if user exists"""
        users = UserStorage.get_all_users()
        return email in users

class DetectionStorage:
    """Handle detection results storage"""
    
    @staticmethod
    def get_user_detections(user_email: str) -> List[Dict[str, Any]]:
        """Get all detections for a user"""
        data = JSONHandler.read_json(DETECTIONS_FILE)
        user_detections = data.get(user_email, [])
        return sorted(user_detections, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    @staticmethod
    def save_detection(user_email: str, detection_data: Dict[str, Any]) -> bool:
        """Save detection result"""
        try:
            data = JSONHandler.read_json(DETECTIONS_FILE)
            if user_email not in data:
                data[user_email] = []
            
            data[user_email].append(detection_data)
            return JSONHandler.write_json(DETECTIONS_FILE, data)
        except Exception as e:
            print(f"Error saving detection: {e}")
            return False
    
    @staticmethod
    def get_detection_count(user_email: str) -> int:
        """Get total detection count for user"""
        detections = DetectionStorage.get_user_detections(user_email)
        return len(detections)
