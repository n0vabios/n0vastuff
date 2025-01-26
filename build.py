import PyInstaller.__main__
import os
import base64
import hashlib
import subprocess
import sys
import shutil
import random
import string
from PIL import Image
import json
from cryptography.fernet import Fernet

def create_security_file():
    security_code = """import base64
import os
import sys
import hashlib
from cryptography.fernet import Fernet
import sys

class SecurityCheck:
    def __init__(self):
        self._key = b'YOUR_GENERATED_KEY_HERE'
        self._cipher = Fernet(self._key)
        
    def _generate_hash(self):
        try:
            # Get the executable path when running as EXE
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
                with open(exe_path, 'rb') as f:
                    content = f.read()
                return hashlib.sha256(content).hexdigest()
            else:
                with open('selfbot.py', 'rb') as f:
                    content = f.read()
                return hashlib.sha256(content).hexdigest()
        except:
            return None
            
    def verify(self):
        try:
            # Get the secure file path
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
                
            secure_file = None
            # Look for the .secure file in subfolders
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    if file.startswith('.') and len(file) > 16:
                        secure_file = os.path.join(root, file)
                        break
                if secure_file:
                    break
                    
            if not secure_file:
                return False
                
            with open(secure_file, 'rb') as f:
                encrypted_hash = f.read()
                
            decrypted_hash = self._cipher.decrypt(encrypted_hash).decode()
            current_hash = self._generate_hash()
            
            return decrypted_hash == current_hash
        except Exception as e:
            print(f"Verification error: {e}")
            return False"""
            
    with open('security.py', 'w') as f:
        f.write(security_code)

def install_requirements():
    print("Installing required packages...")
    try:

        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'cryptography'])
        from cryptography.fernet import Fernet
        

        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        return True
    except Exception as e:
        print(f"Error installing requirements: {e}")
        return False

def generate_secure_files():
    from cryptography.fernet import Fernet
    
    # Create security.py if it doesn't exist
    if not os.path.exists('security.py'):
        create_security_file()
    
    # Generate encryption key
    key = Fernet.generate_key()
    cipher = Fernet(key)
    
    # Calculate file hash
    with open('selfbot.py', 'rb') as f:
        content = f.read()
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Encrypt hash
    encrypted_hash = cipher.encrypt(file_hash.encode())
    
    # Create security folder
    folder_name = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    os.makedirs(folder_name, exist_ok=True)
    
    # Save files directly to the folder
    with open(os.path.join(folder_name, f'.{folder_name}'), 'wb') as f:
        f.write(encrypted_hash)
        
    with open('security.py', 'r') as f:
        security_code = f.read()
    
    security_code = security_code.replace('YOUR_GENERATED_KEY_HERE', str(key))
    
    with open(os.path.join(folder_name, '__init__.py'), 'w') as f:
        f.write(security_code)
    
    # Clean up original security.py
    if os.path.exists('security.py'):
        os.remove('security.py')
    
    return folder_name

def obfuscate_files():

    folder_name = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    os.makedirs(folder_name, exist_ok=True)

    shutil.move('.secure', os.path.join(folder_name, '.'+folder_name))
    shutil.move('security.py', os.path.join(folder_name, '__init__.py'))
    
    return folder_name

def create_default_icon():
    try:
        # Create a 64x64 purple icon
        img = Image.new('RGB', (64, 64), color='purple')
        
        # Save directly to build directory
        os.makedirs('build', exist_ok=True)
        build_icon_path = os.path.join('build', 'icon.ico')
        img.save(build_icon_path, format='ICO')
        
        # Also save to current directory
        img.save('icon.ico', format='ICO')
        
        return build_icon_path
    except Exception as e:
        print(f"Error creating icon: {e}")
        return None

def create_default_config():
    default_config = {
        "token": "",
        "header": {
            "text": "[ n0va.one ]",
            "color": "purple"  
        },
        "footer": {
            "text": "[ made by luxx ]",
            "color": "purple"
        },
        "afk": {
            "enabled": False,
            "message": "I'm currently AFK",
            "pinged_by": []
        },
        "ai": {
            "openai_key": "",
            "last_response": ""
        },
        "message_timer": 5,
        "custom_status_messages": [],
        "hide": {
            "errors": False,
            "status": False
        }
    }
    
    with open('config.json', 'w') as f:
        json.dump(default_config, f, indent=4)

def main():
    try:
        print("Starting build process...")
        
        # Get current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Clean up old files and directories
        for item in ['build', 'dist', '__pycache__', '.secure', 'security.py']:
            try:
                if os.path.isfile(item):
                    os.remove(item)
                elif os.path.isdir(item):
                    shutil.rmtree(item)
            except:
                pass

        # Create required directories
        os.makedirs('dist', exist_ok=True)
        os.makedirs('build', exist_ok=True)

        # Create default config
        config_path = os.path.join(current_dir, 'config.json')
        if not os.path.exists(config_path):
            print("Creating default config.json...")
            create_default_config()

        # Install requirements
        if not install_requirements():
            print("Failed to install requirements. Exiting...")
            sys.exit(1)
        
        print("Generating security files...")
        security_folder = generate_secure_files()
        security_path = os.path.join(current_dir, security_folder)
        
        # Verify security folder exists and has required files
        if not (os.path.exists(security_path) and 
                os.path.exists(os.path.join(security_path, '__init__.py')) and 
                os.path.exists(os.path.join(security_path, f'.{security_folder}'))):
            print(f"Error: Security files not generated correctly")
            sys.exit(1)

        # Create and get icon path
        icon_path = None
        if os.path.exists('icon.ico'):
            icon_path = os.path.abspath('icon.ico')
        else:
            print("Creating default icon...")
            icon_path = create_default_icon()

        print("Building executable...")
        build_args = [
            'selfbot.py',
            '--onefile',
            '--console',
            '--name=n0va_selfbot'
        ]
        
        # Add icon if available
        if icon_path and os.path.exists(icon_path):
            build_args.extend(['--icon', icon_path])
        
        # Add rest of arguments
        build_args.extend([
            '--distpath=./dist',
            '--workpath=./build',
            '--specpath=./build',
            f'--add-data={config_path};.',
            f'--add-data={security_path};{security_folder}',
            '--hidden-import=PIL._tkinter',
            '--hidden-import=win32gui',
            '--hidden-import=win32con',
            '--hidden-import=pystray',
            '--hidden-import=PIL',
            '--hidden-import=bs4',
            '--hidden-import=colorama',
            '--hidden-import=pyfiglet',
            '--hidden-import=win10toast',
            '--hidden-import=cryptography',
            '--hidden-import=discord',
            '--hidden-import=discord.http',
            '--hidden-import=discord.state',
            '--hidden-import=discord.gateway',
            '--hidden-import=aiohttp',
            '--hidden-import=asyncio',
            '--hidden-import=requests',
            '--hidden-import=json',
            '--hidden-import=webbrowser',
            '--hidden-import=datetime',
            '--hidden-import=openai',
            '--hidden-import=base64',
            '--hidden-import=logging',
            '--hidden-import=subprocess',
            '--hidden-import=pkg_resources',
            '--hidden-import=threading',
            '--collect-all=discord',
            '--collect-all=PIL',
            '--collect-all=win32gui',
            '--collect-all=pystray',
            '--collect-all=bs4',
            '--collect-all=colorama',
            '--collect-all=pyfiglet',
            '--collect-all=win10toast',
            '--collect-all=cryptography',
            '--clean'
        ])
        
        # Change to current directory before building
        os.chdir(current_dir)
        PyInstaller.__main__.run(build_args)
        
        if os.path.exists('dist/n0va_selfbot.exe'):
            print("Build completed successfully!")
            
            # Clean up temporary files
            for item in ['.secure', 'security.py', security_folder]:
                try:
                    if os.path.isfile(item):
                        os.remove(item)
                    elif os.path.isdir(item):
                        shutil.rmtree(item)
                except:
                    pass
        else:
            print("Build failed - EXE not created")
            sys.exit(1)
            
    except Exception as e:
        print(f"Build failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 