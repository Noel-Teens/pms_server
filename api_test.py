import requests
import json
import uuid
import sys
import os
import time
from getpass import getpass
from tabulate import tabulate
from colorama import init, Fore, Style

# Initialize colorama
init()

BASE_URL = 'http://localhost:8000/api/'

class APITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.headers = {}
        self.user_role = None
        self.username = None
        self.last_response = None
    
    def login(self, username, password):
        """Login to get authentication token"""
        try:
            print(f"{Fore.CYAN}Attempting to login...{Style.RESET_ALL}")
            response = requests.post(
                f"{self.base_url.replace('/api/', '/auth/')}login/",
                data={'username': username, 'password': password},
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.headers = {'Authorization': f'Token {self.token}'}
                self.username = username
                
                # Get user info to determine role
                user_info = self.get_user_info()
                if user_info:
                    self.user_role = user_info.get('role')
                    role_display = f"{Fore.GREEN}{self.user_role}{Style.RESET_ALL}"
                    print(f"{Fore.GREEN}✅ Logged in as {Fore.YELLOW}{username}{Fore.GREEN} (Role: {role_display}){Style.RESET_ALL}")
                    return True
                return False
            else:
                print(f"{Fore.RED}❌ Login failed: {response.text}{Style.RESET_ALL}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Connection error: Could not connect to the server. Is the server running?{Style.RESET_ALL}")
            return False
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ Timeout: The server took too long to respond.{Style.RESET_ALL}")
            return False
        except Exception as e:
            print(f"{Fore.RED}❌ Error during login: {str(e)}{Style.RESET_ALL}")
            return False
            
    def get_user_info(self):
        """Get current user information"""
        try:
            response = requests.get(
                f"{self.base_url.replace('/api/', '/auth/')}me/",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None
    
    def test_paperworks_list(self):
        """Test getting list of paperworks"""
        try:
            print(f"{Fore.CYAN}Fetching paperworks...{Style.RESET_ALL}")
            response = requests.get(
                f"{self.base_url}paperworks/",
                headers=self.headers,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 200:
                paperworks = response.json()
                print(f"{Fore.GREEN}✅ Retrieved {len(paperworks)} paperworks{Style.RESET_ALL}")
                
                if paperworks:
                    # Display paperworks in a table
                    table_data = []
                    for pw in paperworks:
                        table_data.append([
                            pw.get('id'),
                            pw.get('title'),
                            pw.get('researcher', {}).get('username'),
                            pw.get('status'),
                            pw.get('assigned_at')
                        ])
                    
                    headers = ["ID", "Title", "Researcher", "Status", "Assigned At"]
                    print(tabulate(table_data, headers=headers, tablefmt="grid"))
                
                return paperworks
            else:
                print(f"{Fore.RED}❌ Failed to get paperworks: {response.text}{Style.RESET_ALL}")
                return None
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Connection error: Could not connect to the server.{Style.RESET_ALL}")
            return None
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ Timeout: The server took too long to respond.{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}❌ Error retrieving paperworks: {str(e)}{Style.RESET_ALL}")
            return None
    
    def test_paperwork_detail(self, paperwork_id):
        """Test getting paperwork details"""
        try:
            print(f"{Fore.CYAN}Fetching paperwork details...{Style.RESET_ALL}")
            response = requests.get(
                f"{self.base_url}paperworks/{paperwork_id}/", 
                headers=self.headers,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 200:
                paperwork = response.json()
                print(f"{Fore.GREEN}✅ Retrieved paperwork: {paperwork['title']}{Style.RESET_ALL}")
                
                # Display paperwork details in a formatted way
                print(f"\n{Fore.YELLOW}Paperwork Details:{Style.RESET_ALL}")
                print(f"  {Fore.CYAN}ID:{Style.RESET_ALL} {paperwork.get('id')}")
                print(f"  {Fore.CYAN}Title:{Style.RESET_ALL} {paperwork.get('title')}")
                print(f"  {Fore.CYAN}Researcher:{Style.RESET_ALL} {paperwork.get('researcher', {}).get('username')}")
                print(f"  {Fore.CYAN}Status:{Style.RESET_ALL} {paperwork.get('status')}")
                print(f"  {Fore.CYAN}Assigned At:{Style.RESET_ALL} {paperwork.get('assigned_at')}")
                print(f"  {Fore.CYAN}Updated At:{Style.RESET_ALL} {paperwork.get('updated_at')}")
                
                return paperwork
            else:
                print(f"{Fore.RED}❌ Failed to get paperwork details: {response.text}{Style.RESET_ALL}")
                return None
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Connection error: Could not connect to the server.{Style.RESET_ALL}")
            return None
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ Timeout: The server took too long to respond.{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}❌ Error retrieving paperwork details: {str(e)}{Style.RESET_ALL}")
            return None
    
    def test_versions_list(self, paperwork_id):
        """Test getting versions for a paperwork"""
        try:
            print(f"{Fore.CYAN}Fetching versions for paperwork {paperwork_id}...{Style.RESET_ALL}")
            response = requests.get(
                f"{self.base_url}paperworks/{paperwork_id}/versions/", 
                headers=self.headers,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 200:
                versions = response.json()
                print(f"{Fore.GREEN}✅ Retrieved {len(versions)} versions for paperwork{Style.RESET_ALL}")
                
                if versions:
                    # Display versions in a table
                    table_data = []
                    for v in versions:
                        table_data.append([
                            v.get('version_no'),
                            v.get('submitted_at'),
                            f"{v.get('ai_percent_self', 'N/A')}%",
                            "✓" if v.get('pdf_path') else "✗",
                            "✓" if v.get('latex_path') else "✗",
                            "✓" if v.get('python_path') else "✗"
                        ])
                    
                    headers = ["Version", "Submitted At", "AI %", "PDF", "LaTeX", "Python"]
                    print(tabulate(table_data, headers=headers, tablefmt="grid"))
                
                return versions
            else:
                print(f"{Fore.RED}❌ Failed to get versions: {response.text}{Style.RESET_ALL}")
                return None
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Connection error: Could not connect to the server.{Style.RESET_ALL}")
            return None
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ Timeout: The server took too long to respond.{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}❌ Error retrieving versions: {str(e)}{Style.RESET_ALL}")
            return None
    
    def test_submit_version(self, paperwork_id, version_data):
        """Test submitting a new version"""
        try:
            print(f"{Fore.CYAN}Submitting new version for paperwork {paperwork_id}...{Style.RESET_ALL}")
            response = requests.post(
                f"{self.base_url}paperworks/{paperwork_id}/versions/", 
                headers=self.headers,
                json=version_data,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 201:
                version = response.json()
                print(f"{Fore.GREEN}✅ Submitted new version {version['version_no']}{Style.RESET_ALL}")
                
                # Display version details
                print(f"\n{Fore.YELLOW}Version Details:{Style.RESET_ALL}")
                print(f"  {Fore.CYAN}Version Number:{Style.RESET_ALL} {version.get('version_no')}")
                print(f"  {Fore.CYAN}Submitted At:{Style.RESET_ALL} {version.get('submitted_at')}")
                print(f"  {Fore.CYAN}AI Percentage:{Style.RESET_ALL} {version.get('ai_percent_self')}%")
                print(f"  {Fore.CYAN}PDF Path:{Style.RESET_ALL} {version.get('pdf_path')}")
                print(f"  {Fore.CYAN}LaTeX Path:{Style.RESET_ALL} {version.get('latex_path')}")
                print(f"  {Fore.CYAN}Python Path:{Style.RESET_ALL} {version.get('python_path')}")
                
                return version
            else:
                print(f"{Fore.RED}❌ Failed to submit version: {response.text}{Style.RESET_ALL}")
                return None
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Connection error: Could not connect to the server.{Style.RESET_ALL}")
            return None
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ Timeout: The server took too long to respond.{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}❌ Error submitting version: {str(e)}{Style.RESET_ALL}")
            return None
    
    def test_version_detail(self, paperwork_id, version_no):
        """Test getting version details"""
        try:
            print(f"{Fore.CYAN}Fetching version {version_no} details for paperwork {paperwork_id}...{Style.RESET_ALL}")
            response = requests.get(
                f"{self.base_url}paperworks/{paperwork_id}/versions/{version_no}/", 
                headers=self.headers,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 200:
                version = response.json()
                print(f"{Fore.GREEN}✅ Retrieved version {version['version_no']} details{Style.RESET_ALL}")
                
                # Display version details
                print(f"\n{Fore.YELLOW}Version Details:{Style.RESET_ALL}")
                print(f"  {Fore.CYAN}Version Number:{Style.RESET_ALL} {version.get('version_no')}")
                print(f"  {Fore.CYAN}Submitted At:{Style.RESET_ALL} {version.get('submitted_at')}")
                print(f"  {Fore.CYAN}AI Percentage:{Style.RESET_ALL} {version.get('ai_percent_self')}%")
                print(f"  {Fore.CYAN}PDF Path:{Style.RESET_ALL} {version.get('pdf_path')}")
                print(f"  {Fore.CYAN}LaTeX Path:{Style.RESET_ALL} {version.get('latex_path')}")
                print(f"  {Fore.CYAN}Python Path:{Style.RESET_ALL} {version.get('python_path')}")
                
                if 'paperwork' in version:
                    print(f"\n{Fore.YELLOW}Associated Paperwork:{Style.RESET_ALL}")
                    print(f"  {Fore.CYAN}Title:{Style.RESET_ALL} {version['paperwork'].get('title')}")
                    print(f"  {Fore.CYAN}Status:{Style.RESET_ALL} {version['paperwork'].get('status')}")
                    print(f"  {Fore.CYAN}Researcher:{Style.RESET_ALL} {version['paperwork'].get('researcher_name')}")
                
                return version
            else:
                print(f"{Fore.RED}❌ Failed to get version details: {response.text}{Style.RESET_ALL}")
                return None
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Connection error: Could not connect to the server.{Style.RESET_ALL}")
            return None
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ Timeout: The server took too long to respond.{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}❌ Error retrieving version details: {str(e)}{Style.RESET_ALL}")
            return None
    
    def test_review_paperwork(self, paperwork_id, review_data):
        """Test reviewing a paperwork"""
        try:
            print(f"{Fore.CYAN}Reviewing paperwork {paperwork_id}...{Style.RESET_ALL}")
            response = requests.post(
                f"{self.base_url}paperworks/{paperwork_id}/review/", 
                headers=self.headers,
                json=review_data,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 200:
                paperwork = response.json()
                print(f"{Fore.GREEN}✅ Reviewed paperwork: {paperwork['title']} - Status: {paperwork['status']}{Style.RESET_ALL}")
                
                # Display paperwork details
                print(f"\n{Fore.YELLOW}Updated Paperwork Details:{Style.RESET_ALL}")
                print(f"  {Fore.CYAN}Title:{Style.RESET_ALL} {paperwork.get('title')}")
                print(f"  {Fore.CYAN}Status:{Style.RESET_ALL} {paperwork.get('status')}")
                print(f"  {Fore.CYAN}Researcher:{Style.RESET_ALL} {paperwork.get('researcher', {}).get('username')}")
                print(f"  {Fore.CYAN}Updated At:{Style.RESET_ALL} {paperwork.get('updated_at')}")
                
                if 'comments' in review_data and review_data['comments']:
                    print(f"  {Fore.CYAN}Comments:{Style.RESET_ALL} {review_data['comments']}")
                
                return paperwork
            else:
                print(f"{Fore.RED}❌ Failed to review paperwork: {response.text}{Style.RESET_ALL}")
                return None
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Connection error: Could not connect to the server.{Style.RESET_ALL}")
            return None
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ Timeout: The server took too long to respond.{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}❌ Error reviewing paperwork: {str(e)}{Style.RESET_ALL}")
            return None
    
    def test_reports_summary(self):
        """Test getting reports summary"""
        try:
            print(f"{Fore.CYAN}Fetching reports summary...{Style.RESET_ALL}")
            response = requests.get(
                f"{self.base_url}reports/summary/", 
                headers=self.headers,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 200:
                summary = response.json()
                print(f"{Fore.GREEN}✅ Retrieved reports summary - Total papers: {summary['total_papers']}{Style.RESET_ALL}")
                
                # Display summary details
                print(f"\n{Fore.YELLOW}Summary Statistics:{Style.RESET_ALL}")
                print(f"  {Fore.CYAN}Total Papers:{Style.RESET_ALL} {summary.get('total_papers')}")
                print(f"  {Fore.CYAN}Average AI Percentage:{Style.RESET_ALL} {summary.get('average_ai_percentage', 'N/A')}%")
                
                if 'papers_by_status' in summary:
                    print(f"\n{Fore.YELLOW}Papers by Status:{Style.RESET_ALL}")
                    status_data = []
                    for status, count in summary['papers_by_status'].items():
                        status_data.append([status, count])
                    print(tabulate(status_data, headers=["Status", "Count"], tablefmt="grid"))
                
                return summary
            else:
                print(f"{Fore.RED}❌ Failed to get reports summary: {response.text}{Style.RESET_ALL}")
                return None
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Connection error: Could not connect to the server.{Style.RESET_ALL}")
            return None
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ Timeout: The server took too long to respond.{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}❌ Error retrieving reports summary: {str(e)}{Style.RESET_ALL}")
            return None
    
    def test_notifications_list(self):
        """Test getting notifications"""
        try:
            print(f"{Fore.CYAN}Fetching notifications...{Style.RESET_ALL}")
            response = requests.get(
                f"{self.base_url}notifications/", 
                headers=self.headers,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 200:
                notifications = response.json()
                print(f"{Fore.GREEN}✅ Retrieved {len(notifications)} notifications{Style.RESET_ALL}")
                
                if notifications:
                    # Display notifications in a table
                    table_data = []
                    for notif in notifications:
                        table_data.append([
                            notif.get('id'),
                            notif.get('event'),
                            notif.get('paper', {}).get('title', 'N/A'),
                            notif.get('timestamp')
                        ])
                    
                    headers = ["ID", "Event", "Paper", "Timestamp"]
                    print(tabulate(table_data, headers=headers, tablefmt="grid"))
                else:
                    print(f"{Fore.YELLOW}No notifications found.{Style.RESET_ALL}")
                
                return notifications
            else:
                print(f"{Fore.RED}❌ Failed to get notifications: {response.text}{Style.RESET_ALL}")
                return None
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Connection error: Could not connect to the server.{Style.RESET_ALL}")
            return None
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ Timeout: The server took too long to respond.{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}❌ Error retrieving notifications: {str(e)}{Style.RESET_ALL}")
            return None

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print application header"""
    clear_screen()
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'PMS API TESTING TOOL':^80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")

def main():
    print_header()
    print(f"{Fore.GREEN}Welcome to the PMS API Testing Tool!{Style.RESET_ALL}")
    print(f"This tool allows you to test the API endpoints of the PMS-Backend system.\n")
    
    # Check if server is running
    try:
        requests.get(BASE_URL.rstrip('/'), timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}ERROR: Cannot connect to the server at {BASE_URL}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please make sure the server is running before using this tool.{Style.RESET_ALL}")
        print(f"\nTo start the server, run: {Fore.CYAN}python manage.py runserver{Style.RESET_ALL}")
        sys.exit(1)
    except Exception:
        pass
    
    tester = APITester(BASE_URL)
    
    # Get login credentials
    print(f"\n{Fore.YELLOW}Please login to continue:{Style.RESET_ALL}")
    username = input(f"{Fore.CYAN}Username: {Style.RESET_ALL}")
    password = getpass(f"{Fore.CYAN}Password: {Style.RESET_ALL}")
    
    if not tester.login(username, password):
        print(f"\n{Fore.RED}Login failed. Exiting...{Style.RESET_ALL}")
        time.sleep(2)
        sys.exit(1)
    
    # Store last used paperwork ID for convenience
    last_paperwork_id = None
    
    # Test menu
    while True:
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'API TESTING MENU':^80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        
        # Show user info
        if tester.username and tester.user_role:
            print(f"Logged in as: {Fore.YELLOW}{tester.username}{Style.RESET_ALL} | Role: {Fore.GREEN}{tester.user_role}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}Available Actions:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}1. List all paperworks{Style.RESET_ALL}")
        print(f"{Fore.WHITE}2. Get paperwork details{Style.RESET_ALL}")
        print(f"{Fore.WHITE}3. List versions for a paperwork{Style.RESET_ALL}")
        print(f"{Fore.WHITE}4. Submit a new version{Style.RESET_ALL}")
        print(f"{Fore.WHITE}5. Get version details{Style.RESET_ALL}")
        print(f"{Fore.WHITE}6. Review a paperwork{Style.RESET_ALL}")
        print(f"{Fore.WHITE}7. Get reports summary{Style.RESET_ALL}")
        print(f"{Fore.WHITE}8. List notifications{Style.RESET_ALL}")
        print(f"{Fore.WHITE}9. Clear screen{Style.RESET_ALL}")
        print(f"{Fore.RED}0. Exit{Style.RESET_ALL}")
        
        choice = input(f"\n{Fore.YELLOW}Enter your choice: {Style.RESET_ALL}")
        
        if choice == '1':
            paperworks = tester.test_paperworks_list()
            if paperworks and len(paperworks) > 0:
                # Store the first paperwork ID for convenience
                last_paperwork_id = paperworks[0].get('id')
        
        elif choice == '2':
            if last_paperwork_id:
                print(f"Last used paperwork ID: {Fore.YELLOW}{last_paperwork_id}{Style.RESET_ALL}")
                use_last = input(f"Use this ID? (y/n, default: y): ").lower() != 'n'
                if use_last:
                    paperwork_id = last_paperwork_id
                else:
                    paperwork_id = input(f"{Fore.CYAN}Enter paperwork ID: {Style.RESET_ALL}")
            else:
                paperwork_id = input(f"{Fore.CYAN}Enter paperwork ID: {Style.RESET_ALL}")
            
            paperwork = tester.test_paperwork_detail(paperwork_id)
            if paperwork:
                last_paperwork_id = paperwork_id
        
        elif choice == '3':
            if last_paperwork_id:
                print(f"Last used paperwork ID: {Fore.YELLOW}{last_paperwork_id}{Style.RESET_ALL}")
                use_last = input(f"Use this ID? (y/n, default: y): ").lower() != 'n'
                if use_last:
                    paperwork_id = last_paperwork_id
                else:
                    paperwork_id = input(f"{Fore.CYAN}Enter paperwork ID: {Style.RESET_ALL}")
            else:
                paperwork_id = input(f"{Fore.CYAN}Enter paperwork ID: {Style.RESET_ALL}")
            
            versions = tester.test_versions_list(paperwork_id)
            if versions is not None:
                last_paperwork_id = paperwork_id
        
        elif choice == '4':
            if last_paperwork_id:
                print(f"Last used paperwork ID: {Fore.YELLOW}{last_paperwork_id}{Style.RESET_ALL}")
                use_last = input(f"Use this ID? (y/n, default: y): ").lower() != 'n'
                if use_last:
                    paperwork_id = last_paperwork_id
                else:
                    paperwork_id = input(f"{Fore.CYAN}Enter paperwork ID: {Style.RESET_ALL}")
            else:
                paperwork_id = input(f"{Fore.CYAN}Enter paperwork ID: {Style.RESET_ALL}")
            
            try:
                version_no = int(input(f"{Fore.CYAN}Enter version number: {Style.RESET_ALL}"))
                ai_percent = float(input(f"{Fore.CYAN}Enter AI percentage (0-100): {Style.RESET_ALL}"))
                
                version_data = {
                    'paperwork_id': paperwork_id,
                    'version_no': version_no,
                    'pdf_path': f"uploads/papers/{paperwork_id}/v{version_no}.pdf",
                    'latex_path': f"uploads/papers/{paperwork_id}/v{version_no}.tex",
                    'python_path': f"uploads/papers/{paperwork_id}/v{version_no}.py",
                    'ai_percent_self': ai_percent
                }
                
                version = tester.test_submit_version(paperwork_id, version_data)
                if version is not None:
                    last_paperwork_id = paperwork_id
            except ValueError:
                print(f"{Fore.RED}❌ Invalid input. Please enter numeric values.{Style.RESET_ALL}")
        
        elif choice == '5':
            if last_paperwork_id:
                print(f"Last used paperwork ID: {Fore.YELLOW}{last_paperwork_id}{Style.RESET_ALL}")
                use_last = input(f"Use this ID? (y/n, default: y): ").lower() != 'n'
                if use_last:
                    paperwork_id = last_paperwork_id
                else:
                    paperwork_id = input(f"{Fore.CYAN}Enter paperwork ID: {Style.RESET_ALL}")
            else:
                paperwork_id = input(f"{Fore.CYAN}Enter paperwork ID: {Style.RESET_ALL}")
            
            version_no = input(f"{Fore.CYAN}Enter version number: {Style.RESET_ALL}")
            version = tester.test_version_detail(paperwork_id, version_no)
            if version is not None:
                last_paperwork_id = paperwork_id
        
        elif choice == '6':
            if last_paperwork_id:
                print(f"Last used paperwork ID: {Fore.YELLOW}{last_paperwork_id}{Style.RESET_ALL}")
                use_last = input(f"Use this ID? (y/n, default: y): ").lower() != 'n'
                if use_last:
                    paperwork_id = last_paperwork_id
                else:
                    paperwork_id = input(f"{Fore.CYAN}Enter paperwork ID: {Style.RESET_ALL}")
            else:
                paperwork_id = input(f"{Fore.CYAN}Enter paperwork ID: {Style.RESET_ALL}")
            
            print(f"\n{Fore.YELLOW}Available statuses:{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}ASSIGNED{Style.RESET_ALL} - Paper is assigned to researcher")
            print(f"  {Fore.CYAN}SUBMITTED{Style.RESET_ALL} - Paper has been submitted")
            print(f"  {Fore.CYAN}CHANGES_REQUESTED{Style.RESET_ALL} - Changes have been requested")
            print(f"  {Fore.CYAN}APPROVED{Style.RESET_ALL} - Paper has been approved")
            
            status = input(f"\n{Fore.CYAN}Enter new status: {Style.RESET_ALL}").upper()
            comments = input(f"{Fore.CYAN}Enter comments (optional): {Style.RESET_ALL}")
            
            review_data = {
                'status': status,
                'comments': comments
            }
            
            paperwork = tester.test_review_paperwork(paperwork_id, review_data)
            if paperwork is not None:
                last_paperwork_id = paperwork_id
        
        elif choice == '7':
            tester.test_reports_summary()
        
        elif choice == '8':
            tester.test_notifications_list()
            
        elif choice == '9':
            print_header()
        
        elif choice == '0':
            print(f"{Fore.YELLOW}Exiting...{Style.RESET_ALL}")
            break
        
        else:
            print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
            
        # Pause before showing menu again
        input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")

if __name__ == "__main__":
    main()