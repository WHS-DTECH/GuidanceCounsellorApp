import flet as ft
from dashboard import DashboardView
from search import SearchView
from editor import EditorView
from login import LoginView
from database import StudentBackend
import datetime

class AppController:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "SEND-C"
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT

        # Initialize database
        self.db = StudentBackend() 
        self.current_session_start = None

        async def force_fullscreen_and_load():
            import asyncio
            import ctypes
            
            # Query the actual hardware pixels from the system
            user32 = ctypes.windll.user32
            screen_w = user32.GetSystemMetrics(0)
            screen_h = user32.GetSystemMetrics(1)
            
            # Pass the dimensions to the Flet window BEFORE it is rendered
            self.page.window_width = screen_w
            self.page.window_height = screen_h
            self.page.update()
            
            await asyncio.sleep(0.05)
            
            # NEW: Show the login page first, as soon as the window is ready
            self.show_login()

        # Fire task
        self.page.run_task(force_fullscreen_and_load)

    def login_success(self):
        # Called by handle_login() if username/password are correct
        self.show_dashboard()

    # --- EXISTING NAVIGATION METHODS ---
    def show_dashboard(self):
        if self.page.floating_action_button:
            self.page.floating_action_button.visible = False
        self.page.controls.clear()
        self.page.add(DashboardView(self.page, self))
        self.page.update()

    def go_to_search(self):
        self.page.controls.clear()
        self.page.add(SearchView(self.page, self))
        self.page.update()

    def show_editor(self, student_data=None):
        if self.page.floating_action_button:
            self.page.floating_action_button.visible = False
        self.page.controls.clear()
        self.page.add(EditorView(self.page, self, student_data))
        self.page.update()

    def get_students(self):
        return self.db.get_all_students_list()

    def save_student(self, data):
        self.db.upsert_student(data["student_id"], data)
        self.go_to_search()

    def delete_student(self, student_id):
        if hasattr(self.db, "delete_student"):
            self.db.delete_student(student_id)
        else:
            print(f"[WARNING] 'delete_student' not found in StudentBackend. Check database.py!")
        self.go_to_search()

    def create_new_student_and_edit(self):
        import time
        new_id = f"ST-{int(time.time())}" 
        new_data = {
            "student_id": new_id,
            "full_name": "",
            "preferred_name": "",
            "dob": "",
            "gender": "",
            "ethnicity": "",
            "address": "",
            "phone": "",
            "referral_type": "",
            "whanau": "",
            "care_giver": "",
            "notes": "",
            "sessions": []
        }
        self.show_editor(new_data)

    def start_new_session(self):
        self.current_session_start = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.go_to_search()

    def cancel_session_and_go_back(self):
        self.current_session_start = None
        self.show_dashboard()
    
    def add_custom_option(self, category, value):
        self.db.add_custom_option(category, value)

    def get_custom_options(self, category):
        return self.db.get_custom_options(category)
    
    def show_login(self):
        if self.page.floating_action_button:
            self.page.floating_action_button.visible = False
        self.page.controls.clear()
        
        # Check if a user already exists
        stored_user = self.db.get_stored_user()
        # If stored_user is None, we pass is_registration=True
        is_reg = True if stored_user is None else False
        
        self.page.add(LoginView(self.page, self, is_registration=is_reg))
        self.page.update()

    def register_new_user(self, username, password):
        """Called by LoginView to create the user."""
        self.db.register_user(username, password)
        # Then redirect directly to the dashboard
        self.show_dashboard()

    def verify_login(self, username, password):
        """Checks if the entered data matches the DB."""
        # Directly calls the secure PBKDF2 hash verification in the backend
        return self.db.verify_user_login(username, password)

def main(page: ft.Page):
    AppController(page)

if __name__ == "__main__":
    ft.app(target=main)