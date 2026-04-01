# -*- coding: utf-8 -*-
"""
Custom Classification Manager
Manages user-defined classifications
"""

import json
import os
from qgis.PyQt.QtCore import QSettings


class CustomClassificationManager:
    """Manages user-defined classifications"""

    def __init__(self):
        self.settings = QSettings()
        self.custom_classifications = {}
        self.load_custom_classifications()

    def get_custom_file_path(self):
        """Get path to custom classifications file"""
        plugin_dir = os.path.dirname(__file__)
        return os.path.join(plugin_dir, 'custom_classifications.json')

    def load_custom_classifications(self):
        """Load custom classifications from file"""
        file_path = self.get_custom_file_path()

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.custom_classifications = json.load(f)
            except Exception as e:
                print(f"Error loading custom classifications: {str(e)}")
                self.custom_classifications = {}
        else:
            self.custom_classifications = {}

    def save_custom_classifications(self):
        """Save custom classifications to file"""
        file_path = self.get_custom_file_path()

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.custom_classifications, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving custom classifications: {str(e)}")
            return False

    def add_classification(self, key, classification_info):
        """Add a custom classification"""
        # Validate classification info
        if not self.validate_classification(classification_info):
            return False

        self.custom_classifications[key] = classification_info
        return self.save_custom_classifications()

    def remove_classification(self, key):
        """Remove a custom classification"""
        if key in self.custom_classifications:
            del self.custom_classifications[key]
            return self.save_custom_classifications()
        return False

    def get_classification(self, key):
        """Get a custom classification by key"""
        return self.custom_classifications.get(key, None)

    def get_all_classifications(self):
        """Get all custom classifications"""
        return self.custom_classifications

    def validate_classification(self, classification_info):
        """Validate classification structure"""
        required_keys = ['name', 'description', 'unit', 'ranges']

        # Check required keys
        for key in required_keys:
            if key not in classification_info:
                return False

        # Validate ranges
        if not isinstance(classification_info['ranges'], list):
            return False

        if len(classification_info['ranges']) == 0:
            return False

        # Validate each range
        for range_item in classification_info['ranges']:
            required_range_keys = ['min', 'max', 'label', 'color']
            for key in required_range_keys:
                if key not in range_item:
                    return False

            # Check that min <= max
            try:
                if float(range_item['min']) > float(range_item['max']):
                    return False
            except (ValueError, TypeError):
                return False

            # Validate color format
            color = range_item['color']
            if not (color.startswith('#') and len(color) == 7):
                return False

        return True

    def export_classification(self, key, file_path):
        """Export a classification to JSON file"""
        classification = self.get_classification(key)
        if not classification:
            return False

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({key: classification}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting classification: {str(e)}")
            return False

    def import_classification(self, file_path):
        """Import a classification from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported = json.load(f)

            # Import all classifications from file
            for key, classification in imported.items():
                if self.validate_classification(classification):
                    self.add_classification(key, classification)

            return True
        except Exception as e:
            print(f"Error importing classification: {str(e)}")
            return False
