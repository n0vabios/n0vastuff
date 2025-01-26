import os
import psutil
import time
from colorama import init, Fore, Style

init(autoreset=True)

def find_and_kill_process():
    print(f"{Fore.CYAN}Searching for n0va_selfbot processes...{Style.RESET_ALL}")
    
    found = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'n0va_selfbot' in proc.info['name'].lower():
                print(f"{Fore.YELLOW}Found process: {proc.info['name']} (PID: {proc.info['pid']})")
                proc.kill()
                found = True
                print(f"{Fore.GREEN}Successfully terminated process{Style.RESET_ALL}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    if not found:
        print(f"{Fore.RED}No n0va_selfbot processes found running{Style.RESET_ALL}")

def clean_build_files():
    print(f"\n{Fore.CYAN}Cleaning up build files...{Style.RESET_ALL}")
    
    files_to_remove = [
        'dist/n0va_selfbot.exe',
        'n0va_selfbot.spec',
        '.secure'
    ]
    
    dirs_to_remove = [
        'build',
        'dist',
        '__pycache__'
    ]
    
    # Remove files
    for file in files_to_remove:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"{Fore.GREEN}Removed: {file}")
        except Exception as e:
            print(f"{Fore.RED}Error removing {file}: {e}")
    
    # Remove directories
    for dir in dirs_to_remove:
        try:
            if os.path.exists(dir):
                for root, dirs, files in os.walk(dir, topdown=False):
                    for name in files:
                        try:
                            os.remove(os.path.join(root, name))
                        except:
                            continue
                    for name in dirs:
                        try:
                            os.rmdir(os.path.join(root, name))
                        except:
                            continue
                os.rmdir(dir)
                print(f"{Fore.GREEN}Removed directory: {dir}")
        except Exception as e:
            print(f"{Fore.RED}Error removing directory {dir}: {e}")

def main():
    ascii_art = """
    ███╗   ██╗ ██████╗ ██╗   ██╗ █████╗ 
    ████╗  ██║██╔═████╗██║   ██║██╔══██╗
    ██╔██╗ ██║██║██╔██║██║   ██║███████║
    ██║╚██╗██║████╔╝██║╚██╗ ██╔╝██╔══██║
    ██║ ╚████║╚██████╔╝ ╚████╔╝ ██║  ██║
    ╚═╝  ╚═══╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝
    """
    print(f"{Fore.MAGENTA}{ascii_art}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Force Close Utility{Style.RESET_ALL}")
    
    while True:
        print(f"\n{Fore.YELLOW}Options:{Style.RESET_ALL}")
        print("1. Force close n0va_selfbot")
        print("2. Clean build files")
        print("3. Do both")
        print("4. Exit")
        
        choice = input(f"\n{Fore.GREEN}Enter your choice (1-4): {Style.RESET_ALL}")
        
        if choice == '1':
            find_and_kill_process()
        elif choice == '2':
            clean_build_files()
        elif choice == '3':
            find_and_kill_process()
            time.sleep(1)  # Wait a bit before cleaning
            clean_build_files()
        elif choice == '4':
            print(f"\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
            break
        else:
            print(f"\n{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
        
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Operation cancelled by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}An error occurred: {e}{Style.RESET_ALL}") 