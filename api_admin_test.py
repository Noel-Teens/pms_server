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

BASE_URL = 'http://localhost:8000/'
API_URL = f"{BASE_URL}api/"
ADMIN_URL = f"{BASE_URL}admin_app/"
AUTH_URL = f"{BASE_URL}auth/"

class AdminAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.headers = {}
        self.user_role = None
        self.username = None
        self.last_response = None
        self.researchers = []
        self.paperworks = []
    
    def login(self, username, password):
        """Login to get authentication token"""
        try:
            print(f"{Fore.CYAN}Attempting to login...{Style.RESET_ALL}")
            response = self.session.post(
                f"{AUTH_URL}login/",
                data={'username': username, 'password': password},
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.headers = {'Authorization': f'Token {self.token}'}
                self.username = username
                
                # Assume admin role for this tool after successful login
                self.user_role = 'ADMIN'
                role_display = f"{Fore.GREEN}{self.user_role}{Style.RESET_ALL}"
                print(f"{Fore.GREEN}✅ Logged in as {Fore.YELLOW}{username}{Fore.GREEN} (Role: {role_display}){Style.RESET_ALL}")
                return True
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
            

    
    def create_user(self, username, email, password, role="RESEARCHER", status="ACTIVE"):
        """Create a new user (Admin only)"""
        try:
            print(f"{Fore.CYAN}Creating new user: {username}...{Style.RESET_ALL}")
            
            data = {
                "username": username,
                "email": email,
                "password": password,
                "role": role,
                "status": status
            }
            
            response = requests.post(
                f"{AUTH_URL}register/",
                json=data,
                headers=self.headers,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code in [200, 201]:
                user_data = response.json()
                print(f"{Fore.GREEN}✅ User created successfully: {Fore.YELLOW}{username}{Style.RESET_ALL}")
                
                # If it's a researcher, add to our list
                if role == "RESEARCHER":
                    self.researchers.append(user_data)
                
                return user_data
            else:
                print(f"{Fore.RED}❌ Failed to create user: {response.text}{Style.RESET_ALL}")
                return None
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Connection error: Could not connect to the server.{Style.RESET_ALL}")
            return None
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ Timeout: The server took too long to respond.{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}❌ Error creating user: {str(e)}{Style.RESET_ALL}")
            return None
    
    def update_user_status(self, username, new_status):
        """Update a user's status (Admin only)"""
        try:
            print(f"{Fore.CYAN}Updating status for user {username} to {new_status}...{Style.RESET_ALL}")
            
            data = {"status": new_status}
            
            response = requests.patch(
                f"{ADMIN_URL}users/{username}/status/",
                json=data,
                headers=self.headers,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"{Fore.GREEN}✅ User status updated successfully: {Fore.YELLOW}{username}{Fore.GREEN} → {Fore.YELLOW}{new_status}{Style.RESET_ALL}")
                return user_data
            else:
                print(f"{Fore.RED}❌ Failed to update user status: {response.text}{Style.RESET_ALL}")
                return None
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Connection error: Could not connect to the server.{Style.RESET_ALL}")
            return None
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ Timeout: The server took too long to respond.{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}❌ Error updating user status: {str(e)}{Style.RESET_ALL}")
            return None
    
    def list_users(self):
        """List all users (Admin only)"""
        try:
            print(f"{Fore.CYAN}Fetching users...{Style.RESET_ALL}")
            
            response = requests.get(
                f"{AUTH_URL}users/",
                headers=self.headers,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 200:
                users = response.json()
                print(f"{Fore.GREEN}✅ Retrieved {len(users)} users{Style.RESET_ALL}")
                
                # Store researchers for later use
                self.researchers = [u for u in users if u.get('role') == 'RESEARCHER']
                
                # Display users in a table
                table_data = []
                for user in users:
                    table_data.append([
                        user.get('id', 'N/A'),
                        user.get('username', 'N/A'),
                        user.get('email', 'N/A'),
                        user.get('role', 'N/A'),
                        user.get('status', 'N/A')
                    ])
                
                headers = ["ID", "Username", "Email", "Role", "Status"]
                print(tabulate(table_data, headers=headers, tablefmt="grid"))
                
                return users
            else:
                print(f"{Fore.RED}❌ Failed to get users: {response.text}{Style.RESET_ALL}")
                return None
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Connection error: Could not connect to the server.{Style.RESET_ALL}")
            return None
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ Timeout: The server took too long to respond.{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}❌ Error retrieving users: {str(e)}{Style.RESET_ALL}")
            return None
    
    def assign_paperwork(self, title, researcher_id, deadline=None):
        """Assign a new paperwork to a researcher (Admin only)"""
        try:
            print(f"{Fore.CYAN}Assigning new paperwork: {title}...{Style.RESET_ALL}")
            
            data = {
                "title": title,
                "researcher_id": researcher_id
            }
            
            if deadline:
                data["deadline"] = deadline
            
            response = self.session.post(
                f"{ADMIN_URL}paperworks/",
                json=data,
                headers=self.headers,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code in [200, 201]:
                paperwork = response.json()
                print(f"{Fore.GREEN}✅ Paperwork assigned successfully: {Fore.YELLOW}{title}{Style.RESET_ALL}")
                
                # Add to our list of paperworks
                self.paperworks.append(paperwork)
                
                # Display paperwork details
                print(f"\n{Fore.CYAN}Paperwork Details:{Style.RESET_ALL}")
                print(f"ID: {Fore.YELLOW}{paperwork.get('id')}{Style.RESET_ALL}")
                print(f"Title: {Fore.YELLOW}{paperwork.get('title')}{Style.RESET_ALL}")
                print(f"Status: {Fore.YELLOW}{paperwork.get('status')}{Style.RESET_ALL}")
                print(f"Assigned At: {Fore.YELLOW}{paperwork.get('assigned_at')}{Style.RESET_ALL}")
                if paperwork.get('deadline'):
                    print(f"Deadline: {Fore.YELLOW}{paperwork.get('deadline')}{Style.RESET_ALL}")
                if paperwork.get('deadline'):
                    print(f"Deadline: {Fore.YELLOW}{paperwork.get('deadline')}{Style.RESET_ALL}")
                
                return paperwork
            else:
                print(f"{Fore.RED}❌ Failed to assign paperwork: {response.text}{Style.RESET_ALL}")
                return None
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Connection error: Could not connect to the server.{Style.RESET_ALL}")
            return None
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}❌ Timeout: The server took too long to respond.{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}❌ Error assigning paperwork: {str(e)}{Style.RESET_ALL}")
            return None
    
    def list_paperworks(self):
        """List all paperworks (Admin sees all)"""
        try:
            print(f"{Fore.CYAN}Fetching paperworks...{Style.RESET_ALL}")
            
            response = requests.get(
                f"{API_URL}paperworks/",
                headers=self.headers,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 200:
                paperworks = response.json()
                print(f"{Fore.GREEN}✅ Retrieved {len(paperworks)} paperworks{Style.RESET_ALL}")
                
                # Store for later use
                self.paperworks = paperworks
                
                # Display paperworks in a table
                table_data = []
                for pw in paperworks:
                    table_data.append([
                        pw.get('id'),
                        pw.get('title'),
                        pw.get('researcher', {}).get('username', 'N/A'),
                        pw.get('status')
                    ])
                
                headers = ["ID", "Title", "Researcher", "Status"]
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
    
    def review_paperwork(self, paperwork_id, action, reviewer_notes, ai_percent_verified=None, reassign_to=None):
        """Review a paperwork (Admin only)"""
        try:
            print(f"{Fore.CYAN}Reviewing paperwork {paperwork_id}...{Style.RESET_ALL}")
            
            data = {
                "action": action,
                "reviewer_notes": reviewer_notes
            }
            
            if action == "APPROVE" and ai_percent_verified is not None:
                data["ai_percent_verified"] = ai_percent_verified
            
            if action == "REQUEST_CHANGES" and reassign_to is not None:
                data["reassign_to"] = reassign_to
            
            response = requests.post(
                f"{API_URL}paperworks/{paperwork_id}/review/",
                json=data,
                headers=self.headers,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                status_color = Fore.GREEN if status == "APPROVED" else Fore.YELLOW
                print(f"{Fore.GREEN}✅ Paperwork reviewed successfully. New status: {status_color}{status}{Style.RESET_ALL}")
                
                # Display review details
                print(f"\n{Fore.CYAN}Review Details:{Style.RESET_ALL}")
                print(f"Action: {Fore.YELLOW}{action}{Style.RESET_ALL}")
                print(f"Notes: {Fore.YELLOW}{reviewer_notes}{Style.RESET_ALL}")
                if ai_percent_verified:
                    print(f"AI Percentage: {Fore.YELLOW}{ai_percent_verified}%{Style.RESET_ALL}")
                
                return result
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
    
    def get_reports_summary(self):
        """Get reports summary (Admin only)"""
        try:
            print(f"{Fore.CYAN}Fetching reports summary...{Style.RESET_ALL}")
            
            response = requests.get(
                f"{API_URL}reports/summary/",
                headers=self.headers,
                timeout=10
            )
            
            self.last_response = response
            
            if response.status_code == 200:
                summary = response.json()
                print(f"{Fore.GREEN}✅ Retrieved reports summary{Style.RESET_ALL}")
                
                # Display summary in a table
                table_data = []
                for status, count in summary.items():
                    table_data.append([status, count])
                
                headers = ["Status", "Count"]
                print(tabulate(table_data, headers=headers, tablefmt="grid"))
                
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

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print application header"""
    clear_screen()
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'PMS ADMIN API TESTING TOOL':^80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")

def main():
    print_header()
    print(f"{Fore.GREEN}Welcome to the PMS Admin API Testing Tool!{Style.RESET_ALL}")
    print(f"This tool allows you to test the admin-specific API endpoints of the PMS-Backend system.\n")
    
    # Check if server is running
    try:
        requests.get(BASE_URL, timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}ERROR: Cannot connect to the server at {BASE_URL}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please make sure the server is running before using this tool.{Style.RESET_ALL}")
        print(f"\nTo start the server, run: {Fore.CYAN}python manage.py runserver{Style.RESET_ALL}")
        sys.exit(1)
    except Exception:
        pass
    
    tester = AdminAPITester()
    
    # Get login credentials
    print(f"\n{Fore.YELLOW}Please login with ADMIN credentials:{Style.RESET_ALL}")
    username = input(f"{Fore.CYAN}Username: {Style.RESET_ALL}")
    password = getpass(f"{Fore.CYAN}Password: {Style.RESET_ALL}")
    
    if not tester.login(username, password):
        print(f"\n{Fore.RED}Login failed or user is not an admin. Exiting...{Style.RESET_ALL}")
        time.sleep(2)
        sys.exit(1)
    
    # Store last used IDs for convenience
    last_paperwork_id = None
    last_researcher_id = None
    last_username = None
    
    # Test menu
    while True:
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'ADMIN API TESTING MENU':^80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        
        # Show user info
        if tester.username and tester.user_role:
            print(f"Logged in as: {Fore.YELLOW}{tester.username}{Style.RESET_ALL} | Role: {Fore.GREEN}{tester.user_role}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}User Management:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}1. List all users{Style.RESET_ALL}")
        print(f"{Fore.WHITE}2. Create new user{Style.RESET_ALL}")
        print(f"{Fore.WHITE}3. Update user status{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}Paperwork Management:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}4. List all paperworks{Style.RESET_ALL}")
        print(f"{Fore.WHITE}5. Assign new paperwork{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Reports:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}6. Get reports summary{Style.RESET_ALL}")
        
        print(f"\n{Fore.WHITE}7. Clear screen{Style.RESET_ALL}")
        print(f"{Fore.RED}0. Exit{Style.RESET_ALL}")
        
        choice = input(f"\n{Fore.YELLOW}Enter your choice: {Style.RESET_ALL}")
        
        if choice == '1':
            # List all users
            users = tester.list_users()
            if users and len(users) > 0:
                # Store the first researcher ID for convenience
                researchers = [u for u in users if u.get('role') == 'RESEARCHER']
                if researchers:
                    last_researcher_id = researchers[0].get('id')
                    last_username = researchers[0].get('username')
        
        elif choice == '2':
            # Create new user
            print(f"\n{Fore.CYAN}Create New User:{Style.RESET_ALL}")
            username = input(f"Username: ")
            email = input(f"Email: ")
            password = getpass(f"Password: ")
            
            print(f"\nSelect role:")
            print(f"1. RESEARCHER")
            print(f"2. ADMIN")
            role_choice = input(f"Choice (default: 1): ") or "1"
            role = "ADMIN" if role_choice == "2" else "RESEARCHER"
            
            print(f"\nSelect status:")
            print(f"1. ACTIVE")
            print(f"2. FROZEN")
            print(f"3. INACTIVE")
            status_choice = input(f"Choice (default: 1): ") or "1"
            status = "ACTIVE"
            if status_choice == "2":
                status = "FROZEN"
            elif status_choice == "3":
                status = "INACTIVE"
            
            user = tester.create_user(username, email, password, role, status)
            if user and role == "RESEARCHER":
                last_researcher_id = user.get('id')
                last_username = user.get('username')
        
        elif choice == '3':
            # Update user status
            if last_username:
                print(f"Last used username: {Fore.YELLOW}{last_username}{Style.RESET_ALL}")
                use_last = input(f"Use this username? (y/n, default: y): ").lower() != 'n'
                if use_last:
                    username = last_username
                else:
                    username = input(f"Enter username to update: ")
            else:
                username = input(f"Enter username to update: ")
            
            print(f"\nSelect new status:")
            print(f"1. ACTIVE")
            print(f"2. FROZEN")
            print(f"3. INACTIVE")
            status_choice = input(f"Choice: ")
            status = "ACTIVE"
            if status_choice == "2":
                status = "FROZEN"
            elif status_choice == "3":
                status = "INACTIVE"
            
            tester.update_user_status(username, status)
            last_username = username
        
        elif choice == '4':
            # List all paperworks
            paperworks = tester.list_paperworks()
            if paperworks and len(paperworks) > 0:
                # Store the first paperwork ID for convenience
                last_paperwork_id = paperworks[0].get('id')
        
        elif choice == '5':
            # Assign new paperwork
            if not last_researcher_id:
                # Try to get researchers first
                tester.list_users()
            
            if tester.researchers:
                print(f"\n{Fore.CYAN}Available Researchers:{Style.RESET_ALL}")
                for i, r in enumerate(tester.researchers):
                    print(f"{i+1}. {r.get('username')} (ID: {r.get('id')})")
                
                researcher_choice = input(f"\nSelect researcher (1-{len(tester.researchers)}): ")
                try:
                    idx = int(researcher_choice) - 1
                    if 0 <= idx < len(tester.researchers):
                        researcher_id = tester.researchers[idx].get('id')
                        title = input(f"\nEnter paperwork title: ")
                        deadline_choice = input(f"Set deadline? (y/n, default: n): ").lower()
                        deadline = None
                        if deadline_choice == 'y':
                            deadline_date = input(f"Enter deadline date (YYYY-MM-DD): ")
                            deadline_time = input(f"Enter deadline time (HH:MM): ")
                            deadline = f"{deadline_date}T{deadline_time}:00Z"
                        paperwork = tester.assign_paperwork(title, researcher_id, deadline)
                        if paperwork:
                            last_paperwork_id = paperwork.get('id')
                    else:
                        print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}No researchers available. Please create a researcher first.{Style.RESET_ALL}")
        
        elif choice == '6':
            # Review paperwork
            if not last_paperwork_id:
                # Try to get paperworks first
                tester.list_paperworks()
            
            if tester.paperworks:
                if last_paperwork_id:
                    print(f"Last used paperwork ID: {Fore.YELLOW}{last_paperwork_id}{Style.RESET_ALL}")
                    use_last = input(f"Use this ID? (y/n, default: y): ").lower() != 'n'
                    if use_last:
                        paperwork_id = last_paperwork_id
                    else:
                        paperwork_id = input(f"Enter paperwork ID to review: ")
                else:
                    paperwork_id = input(f"Enter paperwork ID to review: ")
                
                print(f"\nSelect review action:")
                print(f"1. APPROVE")
                print(f"2. REQUEST_CHANGES")
                action_choice = input(f"Choice: ")
                
                if action_choice == "1":
                    action = "APPROVE"
                    ai_percent = input(f"Enter AI percentage verified (0-100): ")
                    try:
                        ai_percent = float(ai_percent)
                        notes = input(f"Enter reviewer notes: ")
                        tester.review_paperwork(paperwork_id, action, notes, ai_percent_verified=ai_percent)
                    except ValueError:
                        print(f"{Fore.RED}Please enter a valid number for AI percentage.{Style.RESET_ALL}")
                elif action_choice == "2":
                    action = "REQUEST_CHANGES"
                    notes = input(f"Enter reviewer notes: ")
                    reassign = input(f"Reassign to another researcher? (y/n, default: n): ").lower() == 'y'
                    
                    if reassign and tester.researchers:
                        print(f"\n{Fore.CYAN}Available Researchers:{Style.RESET_ALL}")
                        for i, r in enumerate(tester.researchers):
                            print(f"{i+1}. {r.get('username')} (ID: {r.get('id')})")
                        
                        researcher_choice = input(f"\nSelect researcher (1-{len(tester.researchers)}): ")
                        try:
                            idx = int(researcher_choice) - 1
                            if 0 <= idx < len(tester.researchers):
                                reassign_to = tester.researchers[idx].get('id')
                                tester.review_paperwork(paperwork_id, action, notes, reassign_to=reassign_to)
                            else:
                                print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
                        except ValueError:
                            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")
                    else:
                        tester.review_paperwork(paperwork_id, action, notes)
                else:
                    print(f"{Fore.RED}Invalid action choice.{Style.RESET_ALL}")
                
                last_paperwork_id = paperwork_id
            else:
                print(f"{Fore.RED}No paperworks available. Please assign a paperwork first.{Style.RESET_ALL}")
        
        elif choice == '7':
            # Get reports summary
            tester.get_reports_summary()
        
        elif choice == '8':
            # Clear screen
            print_header()
        
        elif choice == '0':
            # Exit
            print(f"\n{Fore.GREEN}Thank you for using the PMS Admin API Testing Tool. Goodbye!{Style.RESET_ALL}")
            sys.exit(0)
        
        else:
            print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")

if __name__ == "__main__":
    main()