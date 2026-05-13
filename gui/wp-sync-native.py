#!/usr/bin/python3
"""
WordPress Sync Native GUI
A native desktop application using PyQt5
"""

import sys
import subprocess
import threading
import json
import base64
from pathlib import Path
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QCheckBox, QMessageBox,
    QGroupBox, QFrame, QDialog, QLineEdit, QFormLayout, QDialogButtonBox,
    QFileDialog, QPlainTextEdit, QMenuBar, QAction, QTabWidget, QSpinBox,
    QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QProcess
from PyQt5.QtGui import QFont, QTextCursor, QIcon, QTextCharFormat, QColor

class SettingsManager:
    """Manage application settings"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        # Store settings in user's Application Support directory (persists across app updates)
        self.settings_dir = Path.home() / "Library" / "Application Support" / "Webmix Sync Starter"
        self.settings_file = self.settings_dir / "app-settings.json"
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from file"""
        defaults = {
            "wp_username": "",
            "wp_app_password": "",
            "ssh_key_path": "~/.ssh/id_rsa",
            "default_local_root": "~/Sites",
            "default_sync_items": "themes\nplugins",
            "ssh_port": 22,
            "authenticated": False
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    defaults.update(loaded)
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        return defaults
    
    def save_settings(self):
        """Save settings to file"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set a setting value"""
        self.settings[key] = value
    
    def is_authenticated(self):
        """Check if WordPress credentials are set and authenticated"""
        return self.settings.get('authenticated', False)

class AuthThread(QThread):
    """Thread for WordPress authentication"""
    auth_result = pyqtSignal(bool, str)
    
    def __init__(self, wp_url, username, app_password):
        super().__init__()
        self.wp_url = wp_url
        self.username = username
        self.app_password = app_password
    
    def run(self):
        try:
            # Remove spaces from application password
            clean_password = self.app_password.replace(' ', '')
            
            # Create basic auth header
            credentials = f"{self.username}:{clean_password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded}',
                'Content-Type': 'application/json'
            }
            
            # Test authentication with WordPress REST API
            url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/users/me"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                self.auth_result.emit(True, f"Authenticated as {user_data.get('name', self.username)}")
            else:
                self.auth_result.emit(False, f"Authentication failed: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.auth_result.emit(False, "Connection timeout - check your URL")
        except requests.exceptions.ConnectionError:
            self.auth_result.emit(False, "Cannot connect to WordPress site")
        except Exception as e:
            self.auth_result.emit(False, f"Error: {str(e)}")

class FetchSitesThread(QThread):
    """Thread for fetching sites from WordPress API"""
    sites_result = pyqtSignal(bool, object, str)  # success, data, message
    
    def __init__(self, wp_url, username, app_password):
        super().__init__()
        self.wp_url = wp_url
        self.username = username
        self.app_password = app_password
    
    def run(self):
        try:
            # Remove spaces from application password
            clean_password = self.app_password.replace(' ', '')
            
            # Create basic auth header
            credentials = f"{self.username}:{clean_password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded}',
                'Content-Type': 'application/json'
            }
            
            # Fetch cPanel sites from API
            url = f"{self.wp_url.rstrip('/')}/wp-json/webmix/v1/cpanels"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                sites_data = response.json()
                self.sites_result.emit(True, sites_data, f"Loaded {len(sites_data)} sites from API")
            else:
                self.sites_result.emit(False, None, f"API request failed: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.sites_result.emit(False, None, "Connection timeout")
        except requests.exceptions.ConnectionError:
            self.sites_result.emit(False, None, "Cannot connect to API")
        except Exception as e:
            self.sites_result.emit(False, None, f"Error: {str(e)}")

class SSHTerminalDialog(QDialog):
    """Embedded SSH terminal dialog"""
    
    def __init__(self, ssh_command, site_name, parent=None):
        super().__init__(parent)
        self.ssh_command = ssh_command
        self.site_name = site_name
        self.process = None
        self.init_ui()
        self.start_ssh()
    
    def __del__(self):
        """Destructor - ensure process cleanup"""
        try:
            self.cleanup_process()
        except:
            pass  # Ignore errors during destruction
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle(f"SSH Terminal - {self.site_name}")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Terminal output
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(QFont("Monaco", 11))
        self.terminal_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
        """)
        layout.addWidget(self.terminal_output)
        
        # Input area
        input_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setFont(QFont("Monaco", 11))
        self.input_line.setPlaceholderText("Type command and press Enter...")
        self.input_line.returnPressed.connect(self.send_command)
        input_layout.addWidget(self.input_line)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_command)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        # Status and close
        button_layout = QHBoxLayout()
        self.status_label = QLabel("Connecting...")
        button_layout.addWidget(self.status_label)
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close_terminal)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def start_ssh(self):
        """Start the SSH process"""
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.finished.connect(self.on_process_finished)
        self.process.errorOccurred.connect(self.on_process_error)
        
        # Parse SSH command
        cmd_parts = self.ssh_command.split()
        program = cmd_parts[0]
        args = cmd_parts[1:]
        
        self.append_output(f"Connecting to {self.site_name}...\n")
        self.append_output(f"$ {self.ssh_command}\n\n")
        
        self.process.start(program, args)
        
        if self.process.waitForStarted():
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green;")
            self.input_line.setFocus()
        else:
            self.status_label.setText("Failed to start")
            self.status_label.setStyleSheet("color: red;")
    
    def handle_output(self):
        """Handle output from SSH process"""
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode('utf-8', errors='replace')
        self.append_output(text)
    
    def append_output(self, text):
        """Append text to terminal output"""
        self.terminal_output.moveCursor(QTextCursor.End)
        self.terminal_output.insertPlainText(text)
        self.terminal_output.moveCursor(QTextCursor.End)
    
    def send_command(self):
        """Send command to SSH process"""
        if not self.process or self.process.state() != QProcess.Running:
            QMessageBox.warning(self, "Not Connected", "SSH connection is not active.")
            return
        
        command = self.input_line.text()
        if command:
            # Echo the command locally
            self.append_output(f"$ {command}\n")
            
            # Send to SSH process
            self.process.write(f"{command}\n".encode())
            self.input_line.clear()
    
    def on_process_finished(self, exit_code, exit_status):
        """Handle process termination"""
        self.append_output(f"\n[Connection closed - exit code: {exit_code}]\n")
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: red;")
        self.input_line.setEnabled(False)
        self.send_btn.setEnabled(False)
    
    def on_process_error(self, error):
        """Handle process errors"""
        error_messages = {
            QProcess.FailedToStart: "Failed to start SSH",
            QProcess.Crashed: "SSH process crashed",
            QProcess.Timedout: "SSH process timed out",
            QProcess.WriteError: "Write error",
            QProcess.ReadError: "Read error",
            QProcess.UnknownError: "Unknown error"
        }
        msg = error_messages.get(error, "Unknown error")
        self.append_output(f"\n[ERROR: {msg}]\n")
        self.status_label.setText("Error")
        self.status_label.setStyleSheet("color: red;")
    
    def close_terminal(self):
        """Close the terminal and SSH connection"""
        self.cleanup_process()
        self.close()
    
    def cleanup_process(self):
        """Clean up the SSH process"""
        if not self.process:
            return
        
        # Block all signals to prevent interference during cleanup
        self.process.blockSignals(True)
        
        # Force kill the process if running
        if self.process.state() == QProcess.Running:
            try:
                # Try exit first
                self.process.write(b"exit\n")
                self.process.closeWriteChannel()
                
                # Wait briefly for graceful exit
                if not self.process.waitForFinished(1000):
                    # Force terminate
                    self.process.terminate()
                    
                    # Wait for termination
                    if not self.process.waitForFinished(2000):
                        # Force kill as last resort
                        self.process.kill()
                        # Must wait for kill to complete
                        self.process.waitForFinished(3000)
            except:
                # If anything fails, force kill
                try:
                    self.process.kill()
                    self.process.waitForFinished(3000)
                except:
                    pass
    
    def closeEvent(self, event):
        """Handle dialog close"""
        # Ensure process is fully stopped before closing
        self.cleanup_process()
        # Let the dialog close - process will be destroyed with it
        event.accept()

class ConfigureSiteDialog(QDialog):
    """Dialog for configuring a site pulled from API"""
    
    def __init__(self, site_data, settings_manager, parent=None):
        super().__init__(parent)
        self.site_data = site_data
        self.settings_manager = settings_manager
        self.setWindowTitle(f"Configure Site: {site_data.get('title', 'Unknown')}")
        self.setMinimumWidth(600)
        self.init_ui()
        self.load_defaults()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Site info from API (read-only)
        info_group = QGroupBox("Site Information (from API)")
        info_layout = QFormLayout()
        
        site_title = self.site_data.get('title', 'Unknown')
        server_list = self.site_data.get('server', [])
        server_info = server_list[0] if server_list else {}
        server_name = server_info.get('title', 'Unknown')
        server_ip = server_info.get('ip', 'Unknown')
        
        info_layout.addRow("Site Name:", QLabel(f"<b>{site_title}</b>"))
        info_layout.addRow("Server:", QLabel(server_name))
        info_layout.addRow("Server IP:", QLabel(server_ip))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Configuration form
        config_group = QGroupBox("Sync Configuration")
        config_layout = QFormLayout()
        
        # SSH User
        self.ssh_user_input = QLineEdit()
        self.ssh_user_input.setPlaceholderText("e.g., cpanel-username")
        config_layout.addRow("SSH User:", self.ssh_user_input)
        
        # SSH Port
        self.ssh_port_input = QLineEdit()
        self.ssh_port_input.setPlaceholderText("22")
        config_layout.addRow("SSH Port:", self.ssh_port_input)
        
        # Local root with browse button
        local_layout = QHBoxLayout()
        self.local_root_input = QLineEdit()
        self.local_root_input.setPlaceholderText(f"~/Sites/{site_title}")
        local_layout.addWidget(self.local_root_input)
        browse_local_btn = QPushButton("Browse...")
        browse_local_btn.clicked.connect(self.browse_local_root)
        local_layout.addWidget(browse_local_btn)
        config_layout.addRow("Local Root:", local_layout)
        
        # Remote root
        self.remote_root_input = QLineEdit()
        self.remote_root_input.setPlaceholderText("e.g., /home/user/public_html/wp-content")
        config_layout.addRow("Remote Root:", self.remote_root_input)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Sync items
        layout.addWidget(QLabel("Sync Items (one per line):"))
        self.sync_items_input = QPlainTextEdit()
        self.sync_items_input.setPlaceholderText("themes\nplugins")
        self.sync_items_input.setMaximumHeight(100)
        layout.addWidget(self.sync_items_input)
        
        # Delete option
        self.delete_check = QCheckBox("Enable delete sync (dangerous)")
        layout.addWidget(self.delete_check)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_defaults(self):
        """Load default values from settings"""
        site_title = self.site_data.get('title', '')
        server_list = self.site_data.get('server', [])
        server_ip = server_list[0].get('ip', '') if server_list else ''
        
        # Try to load existing config if it exists
        existing_config = self.load_existing_config(site_title)
        
        if existing_config:
            # Load from existing config
            self.ssh_user_input.setText(existing_config.get('SSH_USER', ''))
            self.ssh_port_input.setText(existing_config.get('SSH_PORT', '22'))
            self.local_root_input.setText(existing_config.get('LOCAL_ROOT', ''))
            self.remote_root_input.setText(existing_config.get('REMOTE_ROOT', ''))
            self.sync_items_input.setPlainText(existing_config.get('SYNC_ITEMS', '').replace(' ', '\n'))
            self.delete_check.setChecked(existing_config.get('RSYNC_DELETE', '0') == '1')
        else:
            # Load defaults from settings
            # Auto-fill SSH user with site name
            self.ssh_user_input.setText(site_title)
            
            default_port = self.settings_manager.get('ssh_port', 22)
            self.ssh_port_input.setText(str(default_port))
            
            default_root = self.settings_manager.get('default_local_root', '~/Sites')
            suggested_local = f"{default_root}/{site_title}".replace('//', '/')
            self.local_root_input.setText(suggested_local)
            
            # Auto-fill remote root with standard cPanel path
            suggested_remote = f"/home/{site_title}/public_html/wp-content"
            self.remote_root_input.setText(suggested_remote)
            
            default_sync_items = self.settings_manager.get('default_sync_items', 'themes\nplugins')
            self.sync_items_input.setPlainText(default_sync_items)
    
    def load_existing_config(self, site_key):
        """Try to load existing configuration for this site"""
        from pathlib import Path
        
        # Check Application Support directory first (bundled app or after migration)
        app_support_dir = Path.home() / "Library" / "Application Support" / "Webmix Sync Starter"
        config_file = app_support_dir / "sites" / f"{site_key}.env"
        
        # Fallback to old location (development mode)
        if not config_file.exists():
            if getattr(sys, 'frozen', False):
                config_file = Path(__file__).parent / "config" / "sites" / f"{site_key}.env"
            else:
                config_file = Path(__file__).parent.parent / "config" / "sites" / f"{site_key}.env"
        
        if not config_file.exists():
            return None
        
        config = {}
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"')
        
        return config
    
    def browse_local_root(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Local Root Directory"
        )
        if folder:
            self.local_root_input.setText(folder)
    
    def validate_and_accept(self):
        if not self.ssh_user_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "SSH User is required")
            return
        if not self.local_root_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Local Root is required")
            return
        if not self.remote_root_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Remote Root is required")
            return
        if not self.sync_items_input.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "At least one Sync Item is required")
            return
        
        self.accept()
    
    def get_config(self):
        """Return the configuration"""
        server_list = self.site_data.get('server', [])
        server_ip = server_list[0].get('ip', '') if server_list else ''
        
        # Convert multi-line sync items to space-separated
        sync_items_lines = self.sync_items_input.toPlainText().strip().split('\n')
        sync_items = ' '.join([line.strip() for line in sync_items_lines if line.strip()])
        
        return {
            'site_key': self.site_data.get('title', ''),
            'ssh_host': server_ip,
            'ssh_port': self.ssh_port_input.text().strip(),
            'ssh_user': self.ssh_user_input.text().strip(),
            'local_root': self.local_root_input.text().strip(),
            'remote_root': self.remote_root_input.text().strip(),
            'sync_items': sync_items,
            'rsync_delete': '1' if self.delete_check.isChecked() else '0'
        }

class SettingsDialog(QDialog):
    """Dialog for application settings"""
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Settings")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.auth_thread = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tabs for different settings categories
        tabs = QTabWidget()
        
        # WordPress Authentication Tab
        wp_tab = QWidget()
        wp_layout = QVBoxLayout(wp_tab)
        
        wp_layout.addWidget(QLabel("<b>WordPress Authentication</b>"))
        wp_layout.addWidget(QLabel("These credentials are required to use the application."))
        wp_layout.addSpacing(10)
        
        wp_form = QFormLayout()
        
        self.wp_url_input = QLineEdit()
        self.wp_url_input.setPlaceholderText("https://example.com")
        wp_form.addRow("WordPress URL:", self.wp_url_input)
        
        self.wp_username_input = QLineEdit()
        self.wp_username_input.setPlaceholderText("your-username")
        wp_form.addRow("Username:", self.wp_username_input)
        
        self.wp_password_input = QLineEdit()
        self.wp_password_input.setEchoMode(QLineEdit.Password)
        self.wp_password_input.setPlaceholderText("xxxx xxxx xxxx xxxx xxxx xxxx")
        wp_form.addRow("App Password:", self.wp_password_input)
        
        wp_layout.addLayout(wp_form)
        
        wp_layout.addSpacing(10)
        wp_layout.addWidget(QLabel(
            "<i>How to create an Application Password:</i><br>"
            "1. Go to your WordPress Admin → Users → Profile<br>"
            "2. Scroll to 'Application Passwords' section<br>"
            "3. Enter a name and click 'Add New Application Password'<br>"
            "4. Copy the generated password (spaces are optional)</i>"
        ))
        
        # Test authentication button
        test_btn_layout = QHBoxLayout()
        self.test_auth_btn = QPushButton("Test Authentication")
        self.test_auth_btn.clicked.connect(self.test_authentication)
        test_btn_layout.addWidget(self.test_auth_btn)
        test_btn_layout.addStretch()
        wp_layout.addLayout(test_btn_layout)
        
        self.auth_status_label = QLabel("")
        wp_layout.addWidget(self.auth_status_label)
        
        wp_layout.addStretch()
        tabs.addTab(wp_tab, "WordPress Auth")
        
        # SSH & Sync Settings Tab
        ssh_tab = QWidget()
        ssh_layout = QVBoxLayout(ssh_tab)
        
        ssh_layout.addWidget(QLabel("<b>SSH & Sync Settings</b>"))
        ssh_layout.addSpacing(10)
        
        ssh_form = QFormLayout()
        
        # SSH Key
        ssh_key_layout = QHBoxLayout()
        self.ssh_key_input = QLineEdit()
        self.ssh_key_input.setPlaceholderText("~/.ssh/id_rsa")
        ssh_key_layout.addWidget(self.ssh_key_input)
        browse_key_btn = QPushButton("Browse...")
        browse_key_btn.clicked.connect(self.browse_ssh_key)
        ssh_key_layout.addWidget(browse_key_btn)
        ssh_form.addRow("SSH Key Path:", ssh_key_layout)
        
        # Default SSH Port
        self.ssh_port_input = QSpinBox()
        self.ssh_port_input.setRange(1, 65535)
        self.ssh_port_input.setValue(22)
        ssh_form.addRow("Default SSH Port:", self.ssh_port_input)
        
        # Local Root
        local_root_layout = QHBoxLayout()
        self.local_root_input = QLineEdit()
        self.local_root_input.setPlaceholderText("~/Sites")
        local_root_layout.addWidget(self.local_root_input)
        browse_root_btn = QPushButton("Browse...")
        browse_root_btn.clicked.connect(self.browse_local_root)
        local_root_layout.addWidget(browse_root_btn)
        ssh_form.addRow("Default Local Root:", local_root_layout)
        
        ssh_layout.addLayout(ssh_form)
        
        # Default Sync Items
        ssh_layout.addSpacing(10)
        ssh_layout.addWidget(QLabel("Default Sync Items (one per line):"))
        self.sync_items_input = QPlainTextEdit()
        self.sync_items_input.setPlaceholderText("themes\nplugins")
        self.sync_items_input.setMaximumHeight(150)
        ssh_layout.addWidget(self.sync_items_input)
        
        ssh_layout.addStretch()
        tabs.addTab(ssh_tab, "SSH & Sync")
        
        layout.addWidget(tabs)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.save_and_close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Load current settings
        self.load_current_settings()
    
    def load_current_settings(self):
        """Load current settings into form"""
        self.wp_url_input.setText(self.settings_manager.get('wp_url', ''))
        self.wp_username_input.setText(self.settings_manager.get('wp_username', ''))
        self.wp_password_input.setText(self.settings_manager.get('wp_app_password', ''))
        self.ssh_key_input.setText(self.settings_manager.get('ssh_key_path', '~/.ssh/id_rsa'))
        self.ssh_port_input.setValue(self.settings_manager.get('ssh_port', 22))
        self.local_root_input.setText(self.settings_manager.get('default_local_root', '~/Sites'))
        self.sync_items_input.setPlainText(self.settings_manager.get('default_sync_items', 'themes\nplugins'))
        
        if self.settings_manager.is_authenticated():
            self.auth_status_label.setText("✓ Previously authenticated")
            self.auth_status_label.setStyleSheet("color: green;")
    
    def browse_ssh_key(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select SSH Private Key",
            str(Path.home() / ".ssh"),
            "All Files (*)"
        )
        if file_path:
            self.ssh_key_input.setText(file_path)
    
    def browse_local_root(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Default Local Root Directory"
        )
        if folder:
            self.local_root_input.setText(folder)
    
    def test_authentication(self):
        """Test WordPress authentication"""
        wp_url = self.wp_url_input.text().strip()
        username = self.wp_username_input.text().strip()
        password = self.wp_password_input.text().strip()
        
        if not wp_url or not username or not password:
            QMessageBox.warning(self, "Missing Information", 
                              "Please fill in all WordPress authentication fields.")
            return
        
        self.test_auth_btn.setEnabled(False)
        self.auth_status_label.setText("Testing authentication...")
        self.auth_status_label.setStyleSheet("color: blue;")
        
        self.auth_thread = AuthThread(wp_url, username, password)
        self.auth_thread.auth_result.connect(self.handle_auth_result)
        self.auth_thread.start()
    
    def handle_auth_result(self, success, message):
        """Handle authentication test result"""
        self.test_auth_btn.setEnabled(True)
        
        if success:
            self.auth_status_label.setText(f"✓ {message}")
            self.auth_status_label.setStyleSheet("color: green;")
        else:
            self.auth_status_label.setText(f"✗ {message}")
            self.auth_status_label.setStyleSheet("color: red;")
    
    def closeEvent(self, event):
        """Handle dialog close - wait for auth thread to finish"""
        if self.auth_thread and self.auth_thread.isRunning():
            self.auth_thread.wait(2000)  # Wait up to 2 seconds
        super().closeEvent(event)
    
    def save_and_close(self):
        """Save settings and close dialog"""
        # Wait for any running auth thread to complete
        if self.auth_thread and self.auth_thread.isRunning():
            self.auth_thread.wait(2000)
        
        # Save WordPress settings
        self.settings_manager.set('wp_url', self.wp_url_input.text().strip())
        self.settings_manager.set('wp_username', self.wp_username_input.text().strip())
        self.settings_manager.set('wp_app_password', self.wp_password_input.text().strip())
        
        # Save SSH & Sync settings
        self.settings_manager.set('ssh_key_path', self.ssh_key_input.text().strip())
        self.settings_manager.set('ssh_port', self.ssh_port_input.value())
        self.settings_manager.set('default_local_root', self.local_root_input.text().strip())
        self.settings_manager.set('default_sync_items', self.sync_items_input.toPlainText().strip())
        
        # Mark as unauthenticated - user must test auth to re-enable
        if (self.settings_manager.get('wp_url') and 
            self.settings_manager.get('wp_username') and 
            self.settings_manager.get('wp_app_password')):
            # Keep authenticated status if all fields are filled
            pass
        else:
            self.settings_manager.set('authenticated', False)
        
        if self.settings_manager.save_settings():
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save settings")

class CommandThread(QThread):
    """Thread for running shell commands"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)
    
    def __init__(self, command, cwd):
        super().__init__()
        self.command = command
        self.cwd = cwd
        self.process = None
        
    def run(self):
        try:
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(self.cwd)
            )
            
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_signal.emit(line)
            
            return_code = self.process.wait()
            self.finished_signal.emit(return_code)
            
        except Exception as e:
            self.output_signal.emit(f"\nError: {e}\n")
            self.finished_signal.emit(1)
    
    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()

class NewSiteDialog(QDialog):
    """Dialog for creating a new site configuration"""
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("New Site Configuration")
        self.setMinimumWidth(500)
        self.init_ui()
        self.load_defaults()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout for inputs
        form = QFormLayout()
        
        self.site_key_input = QLineEdit()
        self.site_key_input.setPlaceholderText("e.g., client-name")
        form.addRow("Site Key:", self.site_key_input)
        
        self.ssh_host_input = QLineEdit()
        self.ssh_host_input.setPlaceholderText("e.g., example.com")
        form.addRow("SSH Host:", self.ssh_host_input)
        
        self.ssh_port_input = QLineEdit("22")
        form.addRow("SSH Port:", self.ssh_port_input)
        
        self.ssh_user_input = QLineEdit()
        self.ssh_user_input.setPlaceholderText("e.g., cpaneluser")
        form.addRow("SSH User:", self.ssh_user_input)
        
        # Local root with browse button
        local_layout = QHBoxLayout()
        self.local_root_input = QLineEdit()
        self.local_root_input.setPlaceholderText("e.g., /Users/you/Sites/project/wp-content")
        local_layout.addWidget(self.local_root_input)
        browse_local_btn = QPushButton("Browse...")
        browse_local_btn.clicked.connect(self.browse_local_root)
        local_layout.addWidget(browse_local_btn)
        form.addRow("Local Root:", local_layout)
        
        self.remote_root_input = QLineEdit()
        self.remote_root_input.setPlaceholderText("e.g., /home/user/public_html/wp-content")
        form.addRow("Remote Root:", self.remote_root_input)
        
        layout.addLayout(form)
        
        # Sync items text area
        layout.addWidget(QLabel("Sync Items (one per line):"))
        self.sync_items_input = QPlainTextEdit()
        self.sync_items_input.setPlaceholderText("themes/my-theme\nplugins/my-plugin")
        self.sync_items_input.setMaximumHeight(100)
        layout.addWidget(self.sync_items_input)
        
        # Additional options
        self.delete_check = QCheckBox("Enable delete sync (dangerous)")
        layout.addWidget(self.delete_check)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def browse_local_root(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Local Root Directory"
        )
        if folder:
            self.local_root_input.setText(folder)
    
    def validate_and_accept(self):
        if not self.site_key_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Site Key is required")
            return
        if not self.ssh_host_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "SSH Host is required")
            return
        if not self.ssh_user_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "SSH User is required")
            return
        if not self.local_root_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Local Root is required")
            return
        if not self.remote_root_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Remote Root is required")
            return
        if not self.sync_items_input.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "At least one Sync Item is required")
            return
        
        self.accept()
    
    def get_config(self):
        """Return the configuration as a dictionary"""
        # Convert multi-line sync items to space-separated
        sync_items_lines = self.sync_items_input.toPlainText().strip().split('\n')
        sync_items = ' '.join([line.strip() for line in sync_items_lines if line.strip()])
        
        return {
            'site_key': self.site_key_input.text().strip(),
            'ssh_host': self.ssh_host_input.text().strip(),
            'ssh_port': self.ssh_port_input.text().strip(),
            'ssh_user': self.ssh_user_input.text().strip(),
            'local_root': self.local_root_input.text().strip(),
            'remote_root': self.remote_root_input.text().strip(),
            'sync_items': sync_items,
            'rsync_delete': '1' if self.delete_check.isChecked() else '0'
        }
    
    def load_defaults(self):
        """Load default values from settings"""
        default_port = self.settings_manager.get('ssh_port', 22)
        self.ssh_port_input.setText(str(default_port))
        
        default_sync_items = self.settings_manager.get('default_sync_items', 'themes\nplugins')
        self.sync_items_input.setPlainText(default_sync_items)

class SelectSiteDialog(QDialog):
    """Dialog for selecting a site from available API sites"""
    
    def __init__(self, api_sites_data, configured_sites, parent=None):
        super().__init__(parent)
        self.api_sites_data = api_sites_data
        self.configured_sites = configured_sites
        self.selected_site = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Select Site to Configure")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Instructions
        layout.addWidget(QLabel("Select a site from the API to configure, or use Manual Entry for custom sites (e.g., dev environments):"))
        
        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to filter sites...")
        self.search_input.textChanged.connect(self.filter_sites)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Sites list
        self.sites_list = QListWidget()
        self.sites_list.itemDoubleClicked.connect(self.on_site_double_click)
        layout.addWidget(self.sites_list)
        
        # Populate list
        self.populate_sites()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.manual_btn = QPushButton("Manual Entry...")
        self.manual_btn.clicked.connect(self.on_manual_entry)
        button_layout.addWidget(self.manual_btn)
        
        button_layout.addStretch()
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        button_layout.addWidget(buttons)
        
        layout.addLayout(button_layout)
    
    def populate_sites(self):
        """Populate the sites list"""
        self.sites_list.clear()
        
        # Sort sites alphabetically
        sorted_sites = sorted(self.api_sites_data, key=lambda x: x.get('title', ''))
        
        for site_data in sorted_sites:
            site_key = site_data.get('title', '')
            if not site_key:
                continue
            
            # Mark if already configured
            if site_key in self.configured_sites:
                display_text = f"{site_key} (already configured)"
            else:
                display_text = site_key
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, site_data)
            self.sites_list.addItem(item)
    
    def filter_sites(self, text):
        """Filter sites list based on search text"""
        for i in range(self.sites_list.count()):
            item = self.sites_list.item(i)
            site_data = item.data(Qt.UserRole)
            site_key = site_data.get('title', '').lower()
            item.setHidden(text.lower() not in site_key)
    
    def on_site_double_click(self, item):
        """Handle double-click on a site"""
        self.selected_site = item.data(Qt.UserRole)
        self.accept()
    
    def on_manual_entry(self):
        """Handle manual entry button"""
        # Use a special marker to indicate manual entry
        self.selected_site = {'manual_entry': True}
        self.accept()
    
    def on_accept(self):
        """Handle OK button"""
        current_item = self.sites_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a site to configure.")
            return
        
        self.selected_site = current_item.data(Qt.UserRole)
        self.accept()
    
    def get_selected_site(self):
        """Return the selected site data"""
        return self.selected_site

class WPSyncGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Get project paths - handle both bundled app and development
        if getattr(sys, 'frozen', False):
            # Running as a bundled app (py2app)
            # __file__ points to Resources/wp-sync-native.py
            # So parent is Resources, which is our root for bundled apps
            self.project_root = Path(__file__).parent.resolve()
        else:
            # Running in development mode
            # __file__ points to gui/wp-sync-native.py
            # So parent.parent is the project root
            self.project_root = Path(__file__).parent.parent.resolve()
        
        # Store user data (sites, settings) in Application Support (persists across app updates)
        self.user_data_dir = Path.home() / "Library" / "Application Support" / "Webmix Sync Starter"
        self.sites_dir = self.user_data_dir / "sites"
        self.bin_dir = self.project_root / "bin"
        
        # Migrate old settings/sites to new location if needed
        self.migrate_user_data()
        
        # Initialize settings manager
        self.settings_manager = SettingsManager(self.project_root)
        
        # Thread tracking
        self.current_thread = None
        self.watch_thread = None
        self.startup_auth_thread = None
        self.fetch_sites_thread = None
        self.api_sites_data = []  # Store API sites data
        
        self.init_ui()
        self.load_sites()
        
        # Check authentication on startup
        self.check_authentication()
    
    def migrate_user_data(self):
        """Migrate settings and sites from old locations to new location (Application Support)"""
        import shutil
        
        # Old app name (if renaming from previous version)
        old_app_support_dir = Path.home() / "Library" / "Application Support" / "Webmix Sync Tool"
        
        # Old locations (inside app bundle)
        old_settings_file = self.project_root / "config" / "app-settings.json"
        old_sites_dir = self.project_root / "config" / "sites"
        
        # New locations (Application Support with new app name)
        new_settings_file = self.user_data_dir / "app-settings.json"
        new_sites_dir = self.sites_dir
        
        # Create new directory structure
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # PRIORITY 1: Migrate from old app name in Application Support (e.g., after app rename)
        if old_app_support_dir.exists() and old_app_support_dir != self.user_data_dir:
            old_app_settings = old_app_support_dir / "app-settings.json"
            old_app_sites = old_app_support_dir / "sites"
            
            if old_app_settings.exists() and not new_settings_file.exists():
                try:
                    shutil.copy2(old_app_settings, new_settings_file)
                    print(f"✓ Migrated settings from old app name: {old_app_settings}")
                except Exception as e:
                    print(f"Warning: Could not migrate settings from old app name: {e}")
            
            if old_app_sites.exists() and not new_sites_dir.exists():
                try:
                    shutil.copytree(old_app_sites, new_sites_dir)
                    print(f"✓ Migrated sites from old app name: {old_app_sites}")
                except Exception as e:
                    print(f"Warning: Could not migrate sites from old app name: {e}")
        
        # PRIORITY 2: Migrate from app bundle (first time migration from old versions)
        if old_settings_file.exists() and not new_settings_file.exists():
            try:
                shutil.copy2(old_settings_file, new_settings_file)
                print(f"✓ Migrated settings from {old_settings_file} to {new_settings_file}")
            except Exception as e:
                print(f"Warning: Could not migrate settings: {e}")
        
        # Migrate sites directory if it exists in old location and not in new location
        if old_sites_dir.exists() and not new_sites_dir.exists():
            try:
                shutil.copytree(old_sites_dir, new_sites_dir)
                print(f"✓ Migrated sites from {old_sites_dir} to {new_sites_dir}")
            except Exception as e:
                print(f"Warning: Could not migrate sites: {e}")
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Webmix Sync Starter")
        self.setGeometry(100, 100, 900, 650)
        
        # Set window icon if available
        icon_path = self.project_root / "gui" / "app-icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Apply minimalistic, modern color scheme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #fafafa;
            }
            QGroupBox {
                font-weight: 500;
                font-size: 11px;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 6px;
                color: #1f2937;
            }
            QPushButton {
                background-color: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
                font-size: 11px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
                border-color: #9ca3af;
            }
            QPushButton:pressed {
                background-color: #d1d5db;
            }
            QPushButton:disabled {
                background-color: #6b7280;
                color: #d1d5db;
                border-color: #6b7280;
            }
            QPushButton#pullBtn {
                background-color: #f3f4f6;
                color: #374151;
            }
            QPushButton#pullBtn:hover {
                background-color: #e5e7eb;
            }
            QPushButton#pushBtn {
                background-color: #f3f4f6;
                color: #374151;
            }
            QPushButton#pushBtn:hover {
                background-color: #e5e7eb;
            }
            QPushButton#watchBtn {
                background-color: #fee2e2;
                color: #7f1d1d;
                border: 1px solid #fca5a5;
            }
            QPushButton#watchBtn:hover {
                background-color: #fecaca;
            }
            QPushButton#watchBtnActive {
                background-color: #d1fae5;
                color: #065f46;
                border: 1px solid #6ee7b7;
            }
            QPushButton#watchBtnActive:hover {
                background-color: #a7f3d0;
            }
            QPushButton#maintenanceBtn {
                background-color: #f3f4f6;
                color: #374151;
            }
            QPushButton#maintenanceBtn:hover {
                background-color: #e5e7eb;
            }
            QPushButton#maintenanceBtn:disabled {
                background-color: #6b7280;
                color: #d1d5db;
                border-color: #6b7280;
            }
            QPushButton#devEnvBtn {
                background-color: #f3f4f6;
                color: #374151;
            }
            QPushButton#devEnvBtn:hover {
                background-color: #e5e7eb;
            }
            QPushButton#devEnvBtn:disabled {
                background-color: #6b7280;
                color: #d1d5db;
                border-color: #6b7280;
            }
            QPushButton#secondaryBtn {
                background-color: #ffffff;
                color: #6b7280;
                border: 1px solid #e5e7eb;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #f9fafb;
                color: #374151;
            }
            QComboBox {
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: #ffffff;
                font-size: 11px;
                min-height: 24px;
                color: #1f2937;
            }
            QComboBox:focus {
                border-color: #9ca3af;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QTextEdit {
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                background-color: #f9fafb;
                color: #1f2937;
                font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
            }
            QLabel {
                color: #1f2937;
            }
        """)
        
        # Menu bar
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        
        settings_action = QAction("Preferences...", self)
        settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(settings_action)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Site Configuration Group
        site_group = QGroupBox("Site Configuration")
        site_layout = QVBoxLayout()
        site_layout.setSpacing(8)
        
        # Site selector
        site_select_layout = QHBoxLayout()
        site_select_layout.setSpacing(6)
        site_label = QLabel("Site:")
        site_label.setMinimumWidth(35)
        site_select_layout.addWidget(site_label)
        self.site_combo = QComboBox()
        self.site_combo.setMinimumWidth(200)
        self.site_combo.currentIndexChanged.connect(self.on_site_selected)
        site_select_layout.addWidget(self.site_combo)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("secondaryBtn")
        self.refresh_btn.clicked.connect(self.load_sites)
        site_select_layout.addWidget(self.refresh_btn)
        
        self.new_site_btn = QPushButton("New Site")
        self.new_site_btn.setObjectName("secondaryBtn")
        self.new_site_btn.clicked.connect(self.create_new_site)
        site_select_layout.addWidget(self.new_site_btn)
        
        self.sync_api_btn = QPushButton("Sync API")
        self.sync_api_btn.setObjectName("secondaryBtn")
        self.sync_api_btn.clicked.connect(self.sync_from_api)
        site_select_layout.addWidget(self.sync_api_btn)
        
        self.edit_site_btn = QPushButton("Edit")
        self.edit_site_btn.setObjectName("secondaryBtn")
        self.edit_site_btn.clicked.connect(self.edit_current_site)
        site_select_layout.addWidget(self.edit_site_btn)
        
        site_select_layout.addStretch()
        
        site_layout.addLayout(site_select_layout)
        
        # Site info
        self.site_info_label = QLabel("Select a site")
        self.site_info_label.setStyleSheet("""
            color: #6b7280;
            padding: 6px 8px;
            background-color: #f9fafb;
            border-radius: 4px;
            border: 1px solid #e5e7eb;
            font-size: 11px;
        """)
        site_layout.addWidget(self.site_info_label)
        
        site_group.setLayout(site_layout)
        main_layout.addWidget(site_group)
        
        # Site Actions Group (requires site selection)
        site_actions_group = QGroupBox("Site Actions")
        site_actions_layout = QVBoxLayout()
        site_actions_layout.setSpacing(8)
        
        # Primary sync row
        sync_row = QHBoxLayout()
        sync_row.setSpacing(6)
        
        self.pull_btn = QPushButton("⬇ Pull")
        self.pull_btn.setObjectName("pullBtn")
        self.pull_btn.setMinimumHeight(32)
        self.pull_btn.clicked.connect(self.run_pull)
        sync_row.addWidget(self.pull_btn)
        
        self.push_btn = QPushButton("⬆ Push")
        self.push_btn.setObjectName("pushBtn")
        self.push_btn.setMinimumHeight(32)
        self.push_btn.clicked.connect(self.run_push)
        sync_row.addWidget(self.push_btn)
        
        self.watch_btn = QPushButton("👁 Watch")
        self.watch_btn.setObjectName("watchBtn")
        self.watch_btn.setMinimumHeight(32)
        self.watch_btn.clicked.connect(self.toggle_watch)
        sync_row.addWidget(self.watch_btn)
        
        site_actions_layout.addLayout(sync_row)
        
        # Secondary site actions row
        site_secondary_row = QHBoxLayout()
        site_secondary_row.setSpacing(6)
        
        self.test_connection_btn = QPushButton("🔌 Test Connection")
        self.test_connection_btn.setMinimumHeight(30)
        self.test_connection_btn.clicked.connect(self.test_connection)
        site_secondary_row.addWidget(self.test_connection_btn)
        
        self.maintenance_btn = QPushButton("🔧 Maintenance")
        self.maintenance_btn.setObjectName("maintenanceBtn")
        self.maintenance_btn.setMinimumHeight(30)
        self.maintenance_btn.setEnabled(False)
        self.maintenance_btn.clicked.connect(self.run_maintenance)
        self.maintenance_btn.hide()  # Hidden for now
        site_secondary_row.addWidget(self.maintenance_btn)
        
        self.ssh_btn = QPushButton("🖥 SSH")
        self.ssh_btn.setMinimumHeight(30)
        self.ssh_btn.setEnabled(True)
        self.ssh_btn.clicked.connect(self.open_ssh_terminal)
        site_secondary_row.addWidget(self.ssh_btn)
        
        site_actions_layout.addLayout(site_secondary_row)
        
        site_actions_group.setLayout(site_actions_layout)
        main_layout.addWidget(site_actions_group)
        
        # General Actions Group (always available)
        general_group = QGroupBox("General")
        general_layout = QHBoxLayout()
        general_layout.setSpacing(6)
        
        self.dev_env_btn = QPushButton("🚀 Dev Setup")
        self.dev_env_btn.setObjectName("devEnvBtn")
        self.dev_env_btn.setMinimumHeight(30)
        self.dev_env_btn.setEnabled(False)
        self.dev_env_btn.clicked.connect(self.setup_dev_environment)
        self.dev_env_btn.hide()  # Hidden for now
        general_layout.addWidget(self.dev_env_btn)
        general_layout.addStretch()
        
        general_group.setLayout(general_layout)
        general_group.hide()  # Hide entire group since it's empty now
        main_layout.addWidget(general_group)
        
        # Output Group
        output_group = QGroupBox("Console")
        output_layout = QVBoxLayout()
        output_layout.setSpacing(6)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Monaco", 10))
        self.output_text.setMinimumHeight(240)
        output_layout.addWidget(self.output_text)
        
        # Clear button
        clear_layout = QHBoxLayout()
        clear_layout.addStretch()
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondaryBtn")
        clear_btn.setMaximumWidth(80)
        clear_btn.clicked.connect(self.clear_output)
        clear_layout.addWidget(clear_btn)
        output_layout.addLayout(clear_layout)
        
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # Status bar
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #f9fafb;
                color: #6b7280;
                border-top: 1px solid #e5e7eb;
                font-size: 11px;
            }
        """)
        self.statusBar().showMessage("Ready")
        
        # Initial state
        self.update_button_states(False)
        self.log_output("⚡ Ready\n", "info")
        self.log_output(f"📁 {self.project_root}\n")
    
    def load_sites(self):
        """Load available sites - only showing configured ones in dropdown"""
        # Remember current selection
        current_site = self.site_combo.currentText()
        self.site_combo.clear()
        
        # Get locally configured sites
        configured_sites = set()
        if self.sites_dir.exists():
            site_files = list(self.sites_dir.glob("*.env"))
            configured_sites = {f.stem for f in site_files if f.stem != "example-site"}
        
        if not configured_sites:
            self.log_output("No configured sites.\n", "warning")
            self.log_output("Click 'Sync from API' to load available sites, then '+ New Site' to configure one.\n", "info")
            return
        
        # Sort sites alphabetically
        sorted_sites = sorted(list(configured_sites))
        
        # Add only configured sites
        for site in sorted_sites:
            self.site_combo.addItem(site)
            index = self.site_combo.count() - 1
            self.site_combo.setItemData(index, site)
        
        # Restore previous selection if it still exists
        if current_site:
            for i in range(self.site_combo.count()):
                if self.site_combo.itemData(i) == current_site:
                    self.site_combo.setCurrentIndex(i)
                    break
        
        self.update_button_states(True)
        self.log_output(f"Loaded {len(configured_sites)} configured site(s)\n", "success")
    
    def create_new_site(self):
        """Open dialog to select and configure a new site from API or manual entry"""
        # Check if API sites are loaded
        if not self.api_sites_data:
            reply = QMessageBox.question(
                self, "No Sites Available",
                "No sites available from API.\n\n"
                "Do you want to manually enter site details?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # Manual entry
                self._create_manual_site()
            return
        
        # Get already configured sites
        configured_sites = set()
        if self.sites_dir.exists():
            site_files = list(self.sites_dir.glob("*.env"))
            configured_sites = {f.stem for f in site_files if f.stem != "example-site"}
        
        # Show site selection dialog
        select_dialog = SelectSiteDialog(self.api_sites_data, configured_sites, self)
        if select_dialog.exec_() != QDialog.Accepted:
            return
        
        selected_site = select_dialog.get_selected_site()
        if not selected_site:
            return
        
        # Check if manual entry was selected
        if selected_site.get('manual_entry'):
            self._create_manual_site()
            return
        
        # Show configuration dialog for the selected site from API
        config_dialog = ConfigureSiteDialog(selected_site, self.settings_manager, self)
        if config_dialog.exec_() != QDialog.Accepted:
            return
        
        config = config_dialog.get_config()
        self._save_site_config(config)
    
    def _create_manual_site(self):
        """Create a site with manual entry"""
        dialog = NewSiteDialog(self.settings_manager, self)
        if dialog.exec_() != QDialog.Accepted:
            return
        
        config = dialog.get_config()
        self._save_site_config(config)
    
    def _save_site_config(self, config):
        """Save site configuration to .env file"""
        # Save the configuration
        site_file = self.sites_dir / f"{config['site_key']}.env"
        
        try:
            # Ensure sites directory exists
            self.sites_dir.mkdir(parents=True, exist_ok=True)
            
            # Write the configuration file
            with open(site_file, 'w') as f:
                f.write(f'SITE_KEY="{config["site_key"]}"\n')
                f.write(f'SSH_HOST="{config["ssh_host"]}"\n')
                f.write(f'SSH_PORT="{config["ssh_port"]}"\n')
                f.write(f'SSH_USER="{config["ssh_user"]}"\n')
                f.write(f'LOCAL_ROOT="{config["local_root"]}"\n')
                f.write(f'REMOTE_ROOT="{config["remote_root"]}"\n')
                f.write(f'SYNC_ITEMS="{config["sync_items"]}"\n')
                f.write(f'RSYNC_DELETE="{config["rsync_delete"]}"\n')
                f.write('DEBOUNCE_SECONDS="3"\n')
            
            self.log_output(f"\n✓ Configured site: {config['site_key']}\n", "success")
            
            # Reload sites
            self.load_sites()
            
            # Select the new site
            index = self.site_combo.findText(config['site_key'])
            if index >= 0:
                self.site_combo.setCurrentIndex(index)
            
        except Exception as e:
            self.log_output(f"\n✗ Error configuring site: {e}\n", "error")
            QMessageBox.critical(
                self, "Error",
                f"Failed to save site configuration:\n{e}"
            )
    
    def fetch_sites_from_api_silent(self):
        """Fetch sites from API silently on startup"""
        wp_url = self.settings_manager.get('wp_url', '')
        wp_username = self.settings_manager.get('wp_username', '')
        wp_password = self.settings_manager.get('wp_app_password', '')
        
        if not wp_url or not wp_username or not wp_password:
            return
        
        self.log_output("Loading sites from API...\n", "info")
        self.fetch_sites_thread = FetchSitesThread(wp_url, wp_username, wp_password)
        self.fetch_sites_thread.sites_result.connect(self.handle_api_sites_silent)
        self.fetch_sites_thread.start()
    
    def sync_from_api(self):
        """Fetch sites from WordPress API"""
        wp_url = self.settings_manager.get('wp_url', '')
        wp_username = self.settings_manager.get('wp_username', '')
        wp_password = self.settings_manager.get('wp_app_password', '')
        
        if not wp_url or not wp_username or not wp_password:
            QMessageBox.warning(
                self, "Authentication Required",
                "Please configure WordPress credentials in Settings > Preferences first."
            )
            return
        
        self.log_output("\n[Loading sites from API...]\n", "info")
        self.sync_api_btn.setEnabled(False)
        self.sync_api_btn.setText("Fetching...")
        
        self.fetch_sites_thread = FetchSitesThread(wp_url, wp_username, wp_password)
        self.fetch_sites_thread.sites_result.connect(self.handle_api_sites)
        self.fetch_sites_thread.start()
    
    def handle_api_sites_silent(self, success, sites_data, message):
        """Handle sites fetched from API on startup (silent)"""
        if success:
            self.api_sites_data = sites_data
            self.log_output(f"✓ {message}\n", "success")
        else:
            self.log_output(f"⚠️ Could not load API sites: {message}\n", "warning")
            self.api_sites_data = []
        
        # Load sites (will show all from API, marked as configured or not)
        self.load_sites()
    
    def handle_api_sites(self, success, sites_data, message):
        """Handle sites fetched from API (manual refresh)"""
        self.sync_api_btn.setEnabled(True)
        self.sync_api_btn.setText("Sync from API")
        
        if not success:
            self.log_output(f"✗ {message}\n", "error")
            QMessageBox.critical(self, "API Error", f"Failed to fetch sites:\n{message}")
            return
        
        self.log_output(f"✓ {message}\n", "success")
        self.api_sites_data = sites_data
        
        # Reload sites list
        self.load_sites()
        
        # Show success message
        configured_count = len([site for site in sites_data 
                                if (self.sites_dir / f"{site.get('title', '')}.env").exists()])
        total_count = len(sites_data)
        unconfigured_count = total_count - configured_count
        
        if unconfigured_count > 0:
            QMessageBox.information(
                self, "Sites Loaded",
                f"Loaded {total_count} sites from API.\n\n"
                f"{configured_count} site(s) already configured.\n"
                f"{unconfigured_count} site(s) available to configure.\n\n"
                f"Click '+ New Site' to configure additional sites."
            )
        else:
            QMessageBox.information(
                self, "Sites Loaded",
                f"Loaded {total_count} sites from API.\nAll sites are configured."
            )
    
    def configure_api_site(self, site_data, remaining_sites):
        """Open configuration dialog for an API site"""
        dialog = ConfigureSiteDialog(site_data, self.settings_manager, self)
        
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_config()
            
            # Save the configuration
            site_file = self.sites_dir / f"{config['site_key']}.env"
            
            try:
                # Ensure sites directory exists
                self.sites_dir.mkdir(parents=True, exist_ok=True)
                
                # Write the configuration file
                with open(site_file, 'w') as f:
                    f.write(f'SITE_KEY="{config["site_key"]}"\n')
                    f.write(f'SSH_HOST="{config["ssh_host"]}"\n')
                    f.write(f'SSH_PORT="{config["ssh_port"]}"\n')
                    f.write(f'SSH_USER="{config["ssh_user"]}"\n')
                    f.write(f'LOCAL_ROOT="{config["local_root"]}"\n')
                    f.write(f'REMOTE_ROOT="{config["remote_root"]}"\n')
                    f.write(f'SYNC_ITEMS="{config["sync_items"]}"\n')
                    f.write(f'RSYNC_DELETE="{config["rsync_delete"]}"\n')
                    f.write('DEBOUNCE_SECONDS="3"\n')
                
                self.log_output(f"✓ Configured site: {config['site_key']}\n", "success")
                
                # If there are more sites to configure, ask user
                if remaining_sites:
                    reply = QMessageBox.question(
                        self, "More Sites Available",
                        f"Site '{config['site_key']}' configured.\n\n"
                        f"{len(remaining_sites)} more site(s) need configuration.\n"
                        f"Configure next site: {remaining_sites[0].get('title', 'Unknown')}?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.configure_api_site(remaining_sites[0], remaining_sites[1:])
                    else:
                        self.log_output(f"{len(remaining_sites)} site(s) left unconfigured\n", "warning")
                        self.load_sites()
                else:
                    # All sites configured
                    self.load_sites()
                    QMessageBox.information(
                        self, "All Sites Configured",
                        "All sites from API have been configured!"
                    )
                
            except Exception as e:
                self.log_output(f"✗ Error configuring site: {e}\n", "error")
                QMessageBox.critical(
                    self, "Error",
                    f"Failed to save site configuration:\n{e}"
                )
        else:
            # User cancelled, ask if they want to continue with remaining
            if remaining_sites:
                reply = QMessageBox.question(
                    self, "More Sites Available",
                    f"Skipped '{site_data.get('title', 'Unknown')}'.\n\n"
                    f"{len(remaining_sites)} more site(s) need configuration.\n"
                    f"Continue with next site?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.configure_api_site(remaining_sites[0], remaining_sites[1:])
                else:
                    self.log_output("Stopped configuring sites\n", "warning")
                    self.load_sites()
            else:
                self.load_sites()
    
    def edit_current_site(self):
        """Edit configuration for the currently selected site"""
        site_key = self.site_combo.currentText()
        if not site_key:
            QMessageBox.warning(self, "No Site Selected", "Please select a site to edit.")
            return
        
        site_file = self.sites_dir / f"{site_key}.env"
        if not site_file.exists():
            QMessageBox.warning(
                self, "Site Not Found",
                f"Configuration file not found for '{site_key}'."
            )
            return
        
        # Try to find this site in API data to get server info
        site_data = None
        for api_site in self.api_sites_data:
            if api_site.get('title', '') == site_key:
                site_data = api_site
                break
        
        # If not in API data, create minimal site data from existing config
        if not site_data:
            existing_config = {}
            with open(site_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_config[key.strip()] = value.strip().strip('"')
            
            site_data = {
                'title': site_key,
                'server': [{
                    'title': 'Manual Entry',
                    'ip': existing_config.get('SSH_HOST', '')
                }]
            }
        
        # Open configuration dialog
        dialog = ConfigureSiteDialog(site_data, self.settings_manager, self)
        
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_config()
            
            try:
                # Write the updated configuration
                with open(site_file, 'w') as f:
                    f.write(f'SITE_KEY="{config["site_key"]}"\n')
                    f.write(f'SSH_HOST="{config["ssh_host"]}"\n')
                    f.write(f'SSH_PORT="{config["ssh_port"]}"\n')
                    f.write(f'SSH_USER="{config["ssh_user"]}"\n')
                    f.write(f'LOCAL_ROOT="{config["local_root"]}"\n')
                    f.write(f'REMOTE_ROOT="{config["remote_root"]}"\n')
                    f.write(f'SYNC_ITEMS="{config["sync_items"]}"\n')
                    f.write(f'RSYNC_DELETE="{config["rsync_delete"]}"\n')
                    f.write('DEBOUNCE_SECONDS="3"\n')
                
                self.log_output(f"\n✓ Updated site configuration: {config['site_key']}\n", "success")
                
                # Reload sites to reflect changes
                self.load_sites()
                
                # Reselect the edited site
                index = self.site_combo.findText(config['site_key'])
                if index >= 0:
                    self.site_combo.setCurrentIndex(index)
                
                QMessageBox.information(
                    self, "Success",
                    f"Site '{config['site_key']}' updated successfully!"
                )
                
            except Exception as e:
                self.log_output(f"\n✗ Error updating site: {e}\n", "error")
                QMessageBox.critical(
                    self, "Error",
                    f"Failed to update site configuration:\n{e}"
                )
        
    def on_site_selected(self):
        """Handle site selection"""
        site_key = self.site_combo.currentData()
        if not site_key:
            return
        
        site_file = self.sites_dir / f"{site_key}.env"
        if site_file.exists():
            config = {}
            with open(site_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"')
            
            host = config.get('SSH_HOST', 'N/A')
            user = config.get('SSH_USER', 'N/A')
            port = config.get('SSH_PORT', 'N/A')
            self.site_info_label.setText(f"📡 {user}@{host}:{port}")
            self.site_info_label.setStyleSheet("""
                color: #374151;
                padding: 6px 8px;
                background-color: #f3f4f6;
                border-radius: 4px;
                border: 1px solid #d1d5db;
                font-size: 11px;
            """)
        else:
            self.site_info_label.setText("⚠️ Site needs configuration - click 'Edit Site'")
            self.site_info_label.setStyleSheet("""
                color: #6b7280;
                padding: 6px 8px;
                background-color: #f9fafb;
                border-radius: 4px;
                border: 1px solid #e5e7eb;
                font-size: 11px;
            """)
    
    def check_authentication(self):
        """Check if WordPress authentication is configured"""
        wp_url = self.settings_manager.get('wp_url', '')
        wp_username = self.settings_manager.get('wp_username', '')
        wp_password = self.settings_manager.get('wp_app_password', '')
        
        if not wp_url or not wp_username or not wp_password:
            self.lock_gui("WordPress authentication not configured")
            QMessageBox.warning(
                self, "Authentication Required",
                "WordPress credentials are required to use this application.\n\n"
                "Please configure your WordPress URL, username, and application password "
                "in Settings > Preferences."
            )
            self.open_settings()
        else:
            # Validate credentials
            self.log_output("Validating WordPress credentials...\n", "info")
            self.startup_auth_thread = AuthThread(wp_url, wp_username, wp_password)
            self.startup_auth_thread.auth_result.connect(self.handle_startup_auth)
            self.startup_auth_thread.start()
    
    def handle_startup_auth(self, success, message):
        """Handle authentication result on startup"""
        if success:
            self.log_output(f"✓ {message}\n", "success")
            self.settings_manager.set('authenticated', True)
            self.settings_manager.save_settings()
            self.unlock_gui()
            # Automatically fetch sites from API
            self.fetch_sites_from_api_silent()
        else:
            self.log_output(f"✗ {message}\n", "error")
            self.settings_manager.set('authenticated', False)
            self.settings_manager.save_settings()
            self.lock_gui("WordPress authentication failed")
            QMessageBox.critical(
                self, "Authentication Failed",
                f"Failed to authenticate with WordPress:\n{message}\n\n"
                "The application will be locked until you provide valid credentials.\n"
                "Go to Settings > Preferences to update your credentials."
            )
    
    def lock_gui(self, reason="Not authenticated"):
        """Lock the GUI controls"""
        self.pull_btn.setEnabled(False)
        self.push_btn.setEnabled(False)
        self.watch_btn.setEnabled(False)
        self.ssh_btn.setEnabled(True)
        self.test_connection_btn.setEnabled(False)
        self.site_combo.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.new_site_btn.setEnabled(False)
        self.sync_api_btn.setEnabled(False)
        self.edit_site_btn.setEnabled(False)
        self.statusBar().showMessage(f"🔒 Locked: {reason}")
        self.log_output(f"\n⚠️  GUI locked: {reason}\n", "warning")
    
    def unlock_gui(self):
        """Unlock the GUI controls"""
        self.site_combo.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.new_site_btn.setEnabled(True)
        self.sync_api_btn.setEnabled(True)
        self.edit_site_btn.setEnabled(True)
        self.update_button_states(True)
        self.statusBar().showMessage("Ready")
        self.log_output("✓ GUI unlocked\n", "success")
    
    def open_settings(self):
        """Open the settings dialog"""
        dialog = SettingsDialog(self.settings_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self.log_output("\nSettings saved. Checking authentication...\n", "info")
            # Re-check authentication after settings change
            self.check_authentication()
    
    def update_button_states(self, enabled):
        """Enable or disable action buttons"""
        self.pull_btn.setEnabled(enabled)
        self.push_btn.setEnabled(enabled)
        self.watch_btn.setEnabled(enabled)
        self.test_connection_btn.setEnabled(enabled)
        # Maintenance button only enabled when site is selected
        self.maintenance_btn.setEnabled(False)  # Keep disabled for now
        # SSH and Dev Env buttons stay disabled
        self.ssh_btn.setEnabled(True)
        self.dev_env_btn.setEnabled(False)
    
    def run_pull(self):
        """Execute pull command"""
        site_key = self.site_combo.currentData()
        if not site_key:
            QMessageBox.warning(self, "No Site", "Please select a site first.")
            return
        
        script_path = self.bin_dir / "pull"
        args = [str(script_path), site_key]
        
        self.execute_command(args, "Pull")
    
    def run_push(self):
        """Execute push command"""
        site_key = self.site_combo.currentData()
        if not site_key:
            QMessageBox.warning(self, "No Site", "Please select a site first.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Push",
            "Are you sure you want to push local changes to the remote server?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        
        script_path = self.bin_dir / "push"
        args = [str(script_path), site_key]
        
        self.execute_command(args, "Push")
    
    def run_maintenance(self):
        """Execute maintenance operations (placeholder)"""
        site_key = self.site_combo.currentData()
        if not site_key:
            QMessageBox.warning(self, "No Site", "Please select a site first.")
            return
        
        QMessageBox.information(
            self, "Coming Soon",
            "Maintenance operations functionality will be implemented soon.\n\n"
            f"Selected site: {site_key}"
        )
        self.log_output(f"\n🔧 Maintenance operations - Coming soon for site: {site_key}\n", "info")
    
    def setup_dev_environment(self):
        """Setup development environment (placeholder)"""
        QMessageBox.information(
            self, "Coming Soon",
            "Development environment setup functionality will be implemented soon.\n\n"
            "This will help you quickly set up a local development environment."
        )
        self.log_output(f"\n🚀 Development environment setup - Coming soon\n", "info")
    
    def toggle_watch(self):
        """Start or stop watch mode"""
        if self.watch_thread and self.watch_thread.isRunning():
            self.stop_watch()
        else:
            self.start_watch()
    
    def start_watch(self):
        """Start watch mode"""
        site_key = self.site_combo.currentData()
        if not site_key:
            QMessageBox.warning(self, "No Site", "Please select a site first.")
            return
        
        script_path = self.bin_dir / "watch"
        args = [str(script_path), site_key]
        
        self.log_output(f"\n{'='*60}\n")
        self.log_output(f"Starting watch mode for site: {site_key}\n", "info")
        self.log_output(f"{'='*60}\n\n")
        
        self.watch_thread = CommandThread(args, self.project_root)
        self.watch_thread.output_signal.connect(self.append_output)
        self.watch_thread.finished_signal.connect(self.on_watch_finished)
        self.watch_thread.start()
        
        self.watch_btn.setText("⏹ Stop")
        self.watch_btn.setObjectName("watchBtnActive")
        self.watch_btn.setStyleSheet("")
        self.watch_btn.style().unpolish(self.watch_btn)
        self.watch_btn.style().polish(self.watch_btn)
        self.pull_btn.setEnabled(False)
        self.push_btn.setEnabled(False)
        self.test_connection_btn.setEnabled(False)
        # Keep SSH, maintenance, and dev env buttons disabled
        self.ssh_btn.setEnabled(True)
        self.maintenance_btn.setEnabled(False)
        self.dev_env_btn.setEnabled(False)
        self.statusBar().showMessage("⚡ Watch mode active")
    
    def stop_watch(self):
        """Stop watch mode"""
        if self.watch_thread:
            self.log_output("\nStopping watch mode...\n", "warning")
            self.watch_thread.stop()
            self.watch_thread.wait()
            self.watch_thread = None
        
        self.watch_btn.setText("👁 Watch")
        self.watch_btn.setObjectName("watchBtn")
        self.watch_btn.setStyleSheet("")
        self.watch_btn.style().unpolish(self.watch_btn)
        self.watch_btn.style().polish(self.watch_btn)
        self.pull_btn.setEnabled(True)
        self.push_btn.setEnabled(True)
        self.test_connection_btn.setEnabled(True)
        # Keep SSH, maintenance, and dev env buttons disabled
        self.ssh_btn.setEnabled(True)
        self.maintenance_btn.setEnabled(False)
        self.dev_env_btn.setEnabled(False)
        self.statusBar().showMessage("Watch stopped")
    
    def on_watch_finished(self, return_code):
        """Handle watch mode completion"""
        self.watch_btn.setText("👁 Watch")
        self.watch_btn.setObjectName("watchBtn")
        self.watch_btn.setStyleSheet("")
        self.watch_btn.style().unpolish(self.watch_btn)
        self.watch_btn.style().polish(self.watch_btn)
        self.pull_btn.setEnabled(True)
        self.push_btn.setEnabled(True)
        self.test_connection_btn.setEnabled(True)
        # Keep SSH, maintenance, and dev env buttons disabled
        self.ssh_btn.setEnabled(True)
        self.maintenance_btn.setEnabled(False)
        self.dev_env_btn.setEnabled(False)
        self.statusBar().showMessage("Ready")
    
    def open_ssh_terminal(self):
        """Open an embedded SSH terminal connection to the selected site"""
        site_key = self.site_combo.currentData()
        if not site_key:
            QMessageBox.warning(self, "No Site", "Please select a site first.")
            return
        
        # Read site configuration
        site_file = self.sites_dir / f"{site_key}.env"
        if not site_file.exists():
            QMessageBox.warning(self, "Site Not Found", f"Configuration file not found for {site_key}")
            return
        
        try:
            config = {}
            with open(site_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"')
            
            ssh_host = config.get('SSH_HOST', '')
            ssh_port = config.get('SSH_PORT', '22')
            ssh_user = config.get('SSH_USER', '')
            
            if not ssh_host or not ssh_user:
                QMessageBox.warning(
                    self, "Invalid Configuration",
                    "SSH host and user are required in the site configuration."
                )
                return
            
            # Get SSH key path from settings
            ssh_key = self.settings_manager.get('ssh_key_path', '~/.ssh/id_rsa')
            
            # Build SSH command
            ssh_cmd = f"ssh -p {ssh_port}"
            if ssh_key:
                ssh_cmd += f" -i {ssh_key}"
            ssh_cmd += f" {ssh_user}@{ssh_host}"
            
            # Open embedded terminal dialog
            self.log_output(f"\n→ Opening SSH terminal to {ssh_user}@{ssh_host}:{ssh_port}\n", "info")
            
            terminal_dialog = SSHTerminalDialog(ssh_cmd, site_key, self)
            terminal_dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Failed to open SSH terminal:\n{e}"
            )
            self.log_output(f"\n✗ Error opening SSH terminal: {e}\n", "error")
    
    def test_connection(self):
        """Test SSH connection to the selected site"""
        site_key = self.site_combo.currentData()
        if not site_key:
            QMessageBox.warning(self, "No Site", "Please select a site first.")
            return
        
        # Read site configuration
        site_file = self.sites_dir / f"{site_key}.env"
        if not site_file.exists():
            QMessageBox.warning(self, "Site Not Found", f"Configuration file not found for {site_key}")
            return
        
        try:
            config = {}
            with open(site_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"')
            
            ssh_host = config.get('SSH_HOST', '')
            ssh_port = config.get('SSH_PORT', '22')
            ssh_user = config.get('SSH_USER', '')
            
            if not ssh_host or not ssh_user:
                QMessageBox.warning(
                    self, "Invalid Configuration",
                    "SSH host and user are required in the site configuration."
                )
                return
            
            # Get SSH key path from settings
            ssh_key = self.settings_manager.get('ssh_key_path', '~/.ssh/id_rsa')
            
            # Build SSH test command (just connect and exit)
            ssh_cmd = ['ssh', '-p', ssh_port]
            if ssh_key:
                ssh_cmd.extend(['-i', ssh_key])
            ssh_cmd.extend([
                '-o', 'ConnectTimeout=10',
                '-o', 'BatchMode=yes',
                '-q',
                f"{ssh_user}@{ssh_host}",
                'echo "Connection successful"'
            ])
            
            self.log_output(f"\n→ Testing SSH connection to {ssh_user}@{ssh_host}:{ssh_port}...\n", "info")
            self.test_connection_btn.setEnabled(False)
            self.test_connection_btn.setText("Testing...")
            
            # Run test in background
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            self.test_connection_btn.setEnabled(True)
            self.test_connection_btn.setText("Test Connection")
            
            if result.returncode == 0:
                self.log_output(f"✓ Connection successful!\n", "success")
                QMessageBox.information(
                    self, "Connection Successful",
                    f"Successfully connected to {ssh_user}@{ssh_host}:{ssh_port}\n\n"
                    f"SSH connection is working properly."
                )
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self.log_output(f"✗ Connection failed: {error_msg}\n", "error")
                QMessageBox.warning(
                    self, "Connection Failed",
                    f"Failed to connect to {ssh_user}@{ssh_host}:{ssh_port}\n\n"
                    f"Error: {error_msg}\n\n"
                    f"Please check your SSH configuration and credentials."
                )
                
        except subprocess.TimeoutExpired:
            self.test_connection_btn.setEnabled(True)
            self.test_connection_btn.setText("Test Connection")
            self.log_output(f"✗ Connection timeout\n", "error")
            QMessageBox.warning(
                self, "Connection Timeout",
                f"Connection to {ssh_user}@{ssh_host}:{ssh_port} timed out.\n\n"
                "Please check if the server is accessible."
            )
        except Exception as e:
            self.test_connection_btn.setEnabled(True)
            self.test_connection_btn.setText("Test Connection")
            self.log_output(f"✗ Error testing connection: {e}\n", "error")
            QMessageBox.critical(
                self, "Error",
                f"Failed to test connection:\n{e}"
            )
    
    def execute_command(self, args, action_name):
        """Execute a command in a thread"""
        self.log_output(f"\n{'='*60}\n")
        self.log_output(f"Running {action_name} for site: {self.site_combo.currentText()}\n", "info")
        self.log_output(f"{'='*60}\n\n")
        
        self.update_button_states(False)
        self.statusBar().showMessage(f"Running {action_name}...")
        
        self.current_thread = CommandThread(args, self.project_root)
        self.current_thread.output_signal.connect(self.append_output)
        self.current_thread.finished_signal.connect(
            lambda code: self.on_command_finished(code, action_name)
        )
        self.current_thread.start()
    
    def on_command_finished(self, return_code, action_name):
        """Handle command completion"""
        if return_code == 0:
            self.log_output(f"\n✓ {action_name} completed successfully\n", "success")
            self.statusBar().showMessage("Ready")
        else:
            self.log_output(f"\n✗ {action_name} failed with exit code {return_code}\n", "error")
            self.statusBar().showMessage("Error occurred")
        
        self.update_button_states(True)
        self.current_thread = None
    
    def stop_current_process(self):
        """Stop the currently running process"""
        if self.watch_thread and self.watch_thread.isRunning():
            self.stop_watch()
        elif self.current_thread and self.current_thread.isRunning():
            self.log_output("\nStopping current process...\n", "warning")
            self.current_thread.stop()
            self.current_thread.wait()
            self.current_thread = None
            self.update_button_states(True)
            self.statusBar().showMessage("Stopped")
    
    def log_output(self, text, level=None):
        """Add text to output with optional styling"""
        if level == "error":
            self.output_text.setTextColor(QColor("#dc2626"))  # Red
        elif level == "success":
            self.output_text.setTextColor(QColor("#16a34a"))  # Green
        elif level == "warning":
            self.output_text.setTextColor(QColor("#d97706"))  # Amber
        elif level == "info":
            self.output_text.setTextColor(QColor("#2563eb"))  # Blue
        else:
            self.output_text.setTextColor(QColor("#374151"))  # Dark gray
        
        self.output_text.append(text.rstrip())
        self.output_text.moveCursor(QTextCursor.End)
        self.output_text.setTextColor(QColor("#374151"))
    
    def append_output(self, text):
        """Append output from thread"""
        self.output_text.setTextColor(QColor("#374151"))
        self.output_text.insertPlainText(text)
        self.output_text.moveCursor(QTextCursor.End)
    
    def clear_output(self):
        """Clear the output area"""
        self.output_text.clear()
    
    def closeEvent(self, event):
        """Handle window close"""
        if (self.watch_thread and self.watch_thread.isRunning()):
            reply = QMessageBox.question(
                self, "Watch Running",
                "Watch mode is still running. Stop it and quit?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if self.watch_thread:
                    self.watch_thread.stop()
                    self.watch_thread.wait()
                if self.current_thread:
                    self.current_thread.stop()
                    self.current_thread.wait()
                if self.startup_auth_thread and self.startup_auth_thread.isRunning():
                    self.startup_auth_thread.wait(2000)
                if self.fetch_sites_thread and self.fetch_sites_thread.isRunning():
                    self.fetch_sites_thread.wait(2000)
                event.accept()
            else:
                event.ignore()
        else:
            if self.current_thread:
                self.current_thread.stop()
                self.current_thread.wait()
            if self.startup_auth_thread and self.startup_auth_thread.isRunning():
                self.startup_auth_thread.wait(2000)
            if self.fetch_sites_thread and self.fetch_sites_thread.isRunning():
                self.fetch_sites_thread.wait(2000)
            event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Webmix Sync Starter")
    app.setOrganizationName("Webmix")
    app.setOrganizationDomain("webmix.nl")
    app.setStyle('Fusion')  # Modern look
    
    # Set application icon
    icon_path = Path(__file__).parent / "app-icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    window = WPSyncGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
