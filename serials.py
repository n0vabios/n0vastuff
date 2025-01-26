import random
import string
import json
import os
import pyfiglet
from colorama import Fore, Style, init
import datetime
from typing import Dict, List, Optional
import time

init(autoreset=True)

class SerialManager:
    def __init__(self):
        self.keys_file = "output/keys.json"
        self.keys = self.load_keys()

    def load_keys(self):
        try:
            # Create output directory if it doesn't exist
            os.makedirs('output', exist_ok=True)
            
            # Try to read existing keys
            try:
                with open(self.keys_file, 'r') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                # If file doesn't exist or is invalid, create new empty keys file
                empty_keys = {}
                with open(self.keys_file, 'w') as f:
                    json.dump(empty_keys, f, indent=4)
                return empty_keys
        except Exception as e:
            print(f"Error initializing keys file: {e}")
            return {}

    def save_keys(self):
        try:
            os.makedirs('output', exist_ok=True)
            with open(self.keys_file, 'w') as f:
                json.dump(self.keys, f, indent=4)
        except Exception as e:
            print(f"Error saving keys: {e}")

    def generate_serial(self, duration_days):
        # Generate key in format: N0VA-XXXX-XXXX-XXXX
        characters = string.ascii_uppercase + string.digits
        groups = ['N0VA'] + [
            ''.join(random.choice(characters) for _ in range(4))
            for _ in range(3)
        ]
        serial = '-'.join(groups)
        
        # Set expiry date (-1 duration means never expires)
        if duration_days == -1:
            expiry_date = "never"
        else:
            expiry_date = (datetime.datetime.now() + datetime.timedelta(days=duration_days)).isoformat()
        
        self.keys[serial] = {
            "used_by": None,
            "expiry_date": expiry_date,
            "duration_days": duration_days
        }
        self.save_keys()
        return serial

    def verify_serial(self, serial, user_id):
        if serial not in self.keys:
            return False, "Invalid serial key."
        
        key_data = self.keys[serial]
        
        if key_data["used_by"]:
            return False, "This serial key has already been used."
        
        # Update key data
        key_data["used_by"] = user_id
        self.save_keys()
        
        if key_data["expiry_date"] == "never":
            return True, "Serial key activated successfully! This key never expires."
        else:
            expiry_date = datetime.datetime.fromisoformat(key_data["expiry_date"])
            return True, f"Serial key activated successfully! Expires on {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}"

    def get_user_serial(self, user_id):
        for serial, data in self.keys.items():
            if data["used_by"] == user_id:
                return serial
        return None

    def get_serial_info(self, serial):
        return self.keys.get(serial)

def generate_key():
    """Generate a key in format: N0VA-XXXX-XXXX-XXXX"""
    characters = string.ascii_uppercase + string.digits
    groups = ['N0VA'] + [
        ''.join(random.choice(characters) for _ in range(4))
        for _ in range(3)
    ]
    return '-'.join(groups)

def save_keys(keys):
    with open('output/keys.json', 'w') as f:
        json.dump(keys, f, indent=4)

def load_keys():
    if not os.path.exists('output'):
        os.makedirs('output')
    try:
        with open('output/keys.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"keys": {}}

def validate_key(key):
    """Check if a key is valid and unused"""
    keys_data = load_keys()
    if key in keys_data["keys"]:
        if keys_data["keys"][key]:
            return "DENIED - KEY USED ALREADY"
        else:
            keys_data["keys"][key] = True
            save_keys(keys_data)
            return "Key validated successfully!"
    return "Invalid key"

def count_keys():
    """Count total number of keys"""
    keys_data = load_keys()
    return len(keys_data["keys"])

def main_menu():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        ascii_banner = pyfiglet.figlet_format("n0va keys")
        print(Fore.CYAN + ascii_banner)
        
        print(Fore.YELLOW + "\nOptions:")
        print(Fore.WHITE + "1. Generate Keys")
        print("2. Validate Key")
        print("3. Count Keys")
        print("4. Exit")
        
        choice = input(Fore.GREEN + "\nEnter your choice (1-4): " + Style.RESET_ALL)
        
        if choice == "1":
            num_keys = int(input(Fore.CYAN + "\nHow many keys to generate?: " + Style.RESET_ALL))
            keys_data = load_keys()
            
            print(Fore.MAGENTA + "\nGenerating keys..." + Style.RESET_ALL)
            colors = [Fore.BLUE, Fore.MAGENTA]  # Only blue and purple colors
            
            for i in range(num_keys):
                new_key = generate_key()
                keys_data["keys"][new_key] = False
                
                # Alternate between blue and purple for each key
                color = colors[i % len(colors)]
                print(f"{color}Found Key: {new_key}{Style.RESET_ALL}")
                time.sleep(0.15)
            
            save_keys(keys_data)
            print(Fore.GREEN + f"\nGenerated {num_keys} keys successfully!" + Style.RESET_ALL)

            
        elif choice == "2":
            key = input(Fore.CYAN + "\nEnter key to validate: " + Style.RESET_ALL)
            result = validate_key(key)
            
            if "DENIED" in result:
                print(Fore.RED + f"\n{result}" + Style.RESET_ALL)
            elif "Invalid" in result:
                print(Fore.YELLOW + f"\n{result}" + Style.RESET_ALL)
            else:
                print(Fore.GREEN + f"\n{result}" + Style.RESET_ALL)
                
            input("\nPress Enter to continue...")
            
        elif choice == "3":
            total_keys = count_keys()
            print(Fore.CYAN + f"\nTotal keys in database: {total_keys}" + Style.RESET_ALL)
            input("\nPress Enter to continue...")
            
        elif choice == "4":
            print(Fore.YELLOW + "\nGoodbye!" + Style.RESET_ALL)
            break
        
        else:
            print(Fore.RED + "\nInvalid choice! Please try again." + Style.RESET_ALL)
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main_menu()
