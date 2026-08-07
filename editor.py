import flet as ft
import datetime

class EditorView(ft.Container):
    def __init__(self, page: ft.Page, controller, student_data=None):
        super().__init__()
        self.main_page = page
        self.controller = controller
        self.student_data = student_data
        
        # Design Constants
        self.color_bg = "#F3F4F6"
        self.color_accent = "#22C55E"
        self.color_blue = "#3B82F6"
        self.color_danger = "#EF4444" 
        
        self.expand = True
        self.bgcolor = self.color_bg
        
        # Input dictionary for easy access when saving
        self.inputs = {}
        
        # Dynamic tracking of popup components for updates
        self.menu_buttons = {}
        
        # --- CUSTOM OVERLAY SYSTEM ---
        self.overlay = ft.Container(
            expand=True,
            bgcolor="rgba(0, 0, 0, 0.5)",
            visible=False,
            content=ft.Row(
                controls=[],
                alignment="center",
                vertical_alignment="center"
            )
        )
        
        # UI Structure
        self.content = ft.Stack(
            controls=[
                ft.Row(
                    controls=[
                        self.build_sidebar(),
                        self.build_main_content(),
                    ],
                    spacing=0,
                    expand=True
                ),
                self.overlay
            ],
            expand=True
        )

    def did_mount(self):
        # Once the view is successfully mounted onto the page, safely populate the dropdowns
        for key in list(self.menu_buttons.keys()):
            popup_menu, base_options, allows_custom, category_name, tf = self.menu_buttons[key]
            self.refresh_dropdown(key, category_name, tf)

    # --- HELPER METHOD FOR CUSTOM POPUPS ---
    def show_custom_popup(self, title, message, on_confirm, confirm_text="Yes", content_control=None):
        def close_overlay(e):
            self.overlay.visible = False
            self.update()

        def confirm_wrap(e):
            self.overlay.visible = False
            self.update()
            on_confirm()

        popup_box = ft.Container(
            width=450,
            bgcolor="white",
            border_radius=12,
            padding=25,
            content=ft.Column(
                controls=[
                    ft.Text(title, size=20, weight="bold", color="#0F172A"),
                    ft.Divider(height=10, color="transparent"),
                    # FIX: Removed expand=True from ft.Text to keep the popup container compact
                    content_control if content_control else ft.Text(message, size=15, color="#475569"),
                    ft.Divider(height=10, color="transparent"),
                    ft.Row(
                        controls=[
                            ft.TextButton("Cancel", on_click=close_overlay),
                            ft.ElevatedButton(
                                content=ft.Text(confirm_text, color="white"),
                                bgcolor=self.color_accent if content_control else self.color_danger,
                                on_click=confirm_wrap
                            )
                        ],
                        alignment="end",
                        spacing=15
                    )
                ],
                tight=True
            )
        )
        
        self.overlay.content.controls = [popup_box]
        self.overlay.visible = True
        self.update()

    # --- POPUP FOR ADDING CUSTOM OPTIONS ---
    def show_add_custom_option_dialog(self, key, category, text_field):
        input_field = ft.TextField(label=f"New {category} Entry", autofocus=True)
        
        def save_custom():
            val = input_field.value.strip()
            if val:
                # 1. Save to Database via Controller
                if hasattr(self.controller, "add_custom_option"):
                    self.controller.add_custom_option(category, val)
                
                # 2. Write straight into our profile view
                text_field.value = val
                text_field.update()
                
                # 3. Refresh the specific dropdown options list
                self.refresh_dropdown(key, category, text_field)

        self.show_custom_popup(
            title=f"Add custom template",
            message="",
            on_confirm=save_custom,
            confirm_text="Add Option",
            content_control=input_field
        )

    def build_sidebar(self, active=False):
        return ft.Container(
            width=280,
            bgcolor="#1E293B",
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Text("SEND-C", size=28, weight="bold", color="white"),
                    ft.Divider(height=20, color="transparent"),
                    self.sidebar_item("DASHBOARD", on_click=self.cancel_clicked),
                    self.sidebar_item("STUDENTS", active=True),
                ]
            )
        )

    def sidebar_item(self, text, active=False, on_click=None):
        return ft.Container(
            content=ft.Text(text, color="white" if active else "white70", size=14, weight="bold"),
            padding=15,
            border_radius=10,
            bgcolor="white10" if active else "transparent",
            on_click=on_click
        )

    def get_calculated_age(self, dob_str):
        if not dob_str or not dob_str.strip():
            return "-"
        try:
            birth_date = datetime.datetime.strptime(dob_str.strip(), "%d.%m.%Y")
            today = datetime.datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return str(age) if age >= 0 else "-"
        except ValueError:
            return "-"

    def dob_changed(self, e):
        current_text = e.control.value
        self.inputs["calculated_age"].value = self.get_calculated_age(current_text)
        self.inputs["calculated_age"].update()

    def format_session_time(self, iso_or_raw_str):
        if not iso_or_raw_str or not iso_or_raw_str.strip():
            return ""
        raw_str = iso_or_raw_str.strip()
        try:
            parsed_dt = datetime.datetime.fromisoformat(raw_str[:16].replace(" ", "T"))
            return parsed_dt.strftime("%H:%M %d.%m.%Y")
        except ValueError:
            return raw_str

    def parse_to_iso_session(self, formatted_str):
        try:
            parsed_dt = datetime.datetime.strptime(formatted_str.strip(), "%H:%M %d.%m.%Y")
            return parsed_dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return formatted_str.strip()

    def build_main_content(self):
        data = self.student_data if self.student_data else {}
        
        raw_sessions = data.get("sessions", [])
        if not isinstance(raw_sessions, list):
            raw_sessions = []
            
        formatted_sessions = [self.format_session_time(s) for s in raw_sessions if s]
            
        if hasattr(self.controller, "current_session_start") and self.controller.current_session_start:
            new_session_formatted = self.format_session_time(self.controller.current_session_start)
            formatted_sessions.append(new_session_formatted)
            self.controller.current_session_start = None 
        
        session_string = ", ".join(formatted_sessions)
        session_count = str(len(formatted_sessions))
        
        initial_dob = data.get("dob", "").strip()
        initial_age = self.get_calculated_age(initial_dob)
        
        gender_options = ["Male", "Female", "Other"]
        
        # Default Base lists (will be merged with dynamic custom items from database)
        ethnicity_options = ["NZ European", "Māori"]
        referral_options = ["Family issues"]
        
        is_existing_student = bool(data.get("student_id"))

        return ft.Container(
            expand=True,
            padding=40,
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Row([
                        ft.Text("Edit Student Profile" if is_existing_student else "New Student Profile", size=32, weight="bold", color="#0F172A"),
                        ft.TextButton(
                            content=ft.Text("Delete Profile", color=self.color_danger),
                            on_click=self.show_delete_dialog,
                            visible=is_existing_student
                        ) if is_existing_student else ft.Container()
                    ], alignment="spaceBetween", vertical_alignment="center"),
                    
                    ft.Divider(height=20),
                    
                    ft.Text("Session Tracking", size=18, weight="bold", color=self.color_blue),
                    ft.Row([
                        self.create_input("session_count", "Total Sessions", session_count, width=150),
                        self.create_input("sessions_list", "Session Times (HH:MM DD.MM.YYYY)", session_string, expand=True),
                    ], spacing=15),
                    
                    ft.Divider(height=15, color="transparent"),
                    
                    ft.Text("Core Details", size=18, weight="bold", color="#1E293B"),
                    self.create_input("student_id", "System ID", data.get("student_id", ""), disabled=True),
                    
                    ft.Row([
                        self.create_input("full_name", "Full Name", data.get("full_name", ""), expand=True),
                        self.create_input("preferred_name", "Preferred Name", data.get("preferred_name", ""), expand=True),
                    ], spacing=15),
                    
                    ft.Row([
                        self.create_input("dob", "Date of Birth (DD.MM.YYYY)", initial_dob, expand=True, on_change=self.dob_changed),
                        self.create_input("calculated_age", "Age", initial_age, disabled=True, width=120),
                        self.create_input("gender", "Gender", data.get("gender", ""), options=gender_options, expand=True),
                        self.create_input("ethnicity", "Ethnicity", data.get("ethnicity", ""), options=ethnicity_options, expand=True, allows_custom=True, category_name="Ethnicity"),
                    ], spacing=15),
                    
                    ft.Divider(height=15, color="transparent"),
                    
                    ft.Text("Contact & Relations", size=18, weight="bold", color="#1E293B"),
                    self.create_input("address", "Address", data.get("address", "")),
                    self.create_input("phone", "Phone Numbers", data.get("phone", "")),
                    
                    ft.Row([
                        self.create_input("whanau", "Whānau", data.get("whanau", ""), expand=True),
                        self.create_input("care_giver", "Care Giver", data.get("care_giver", ""), expand=True),
                    ], spacing=15),
                    
                    ft.Divider(height=15, color="transparent"),
                    
                    ft.Text("Referral & Counselor Notes", size=18, weight="bold", color="#1E293B"),
                    self.create_input("referral_type", "Referral Type", data.get("referral_type", ""), options=referral_options, allows_custom=True, category_name="Referral Type"),
                    self.create_input("notes", "Notes about Student", data.get("notes", ""), multiline=True, expand=True),
                    
                    ft.Divider(height=30, color="transparent"),
                    
                    ft.Row([
                        ft.ElevatedButton("CANCEL", on_click=self.cancel_clicked),
                        ft.ElevatedButton(
                            "SAVE STUDENT PROFILE",
                            bgcolor=self.color_accent,
                            color="white",
                            height=50,
                            on_click=self.save_clicked
                        ),
                    ], alignment="end", spacing=20)
                ]
            )
        )

    def create_input(self, key, label, value, disabled=False, multiline=False, width=None, expand=False, options=None, allows_custom=False, category_name=None, on_change=None):
        tf = ft.TextField(
            label=label,
            value=str(value) if value is not None else "",
            disabled=disabled,
            multiline=multiline,
            min_lines=4 if multiline else 1,
            border_color="#CBD5E1",
            focused_border_color="#3B82F6",
            expand=True if options else expand,
            width=width,
            on_change=on_change
        )
        self.inputs[key] = tf
        
        if options:
            popup_menu = ft.PopupMenuButton(
                items=[],
                content=ft.Container(
                    content=ft.Text("Select", color=self.color_blue, weight="bold"),
                    padding=10
                ),
                tooltip="Show suggestions"
            )
            
            # Map structural reference to sync options inside callbacks later
            self.menu_buttons[key] = (popup_menu, options, allows_custom, category_name, tf)
            self.refresh_dropdown(key, category_name, tf)
            
            return ft.Row(
                controls=[tf, popup_menu],
                spacing=5,
                expand=expand,
                vertical_alignment="center"
            )
            
        return tf

    # --- GENERATE & SYNCHRONIZE DROPDOWNS ---
    def refresh_dropdown(self, key, category, text_field):
        if key not in self.menu_buttons:
            return
            
        popup_menu, base_options, allows_custom, category_name, tf = self.menu_buttons[key]
        menu_items = []
        
        # 1. Action point button: "Add Dynamic Element" at top
        # FIX: Avoid using icons for maximum compatibility with older Flet versions
        if allows_custom and category_name:
            menu_items.append(
                ft.PopupMenuItem(
                    content=ft.Text("[+] Add Custom...", color=self.color_accent, weight="bold"),
                    on_click=lambda e: self.show_add_custom_option_dialog(key, category_name, text_field)
                )
            )

        # 2. Add structural built-in static option list array
        for opt in base_options:
            menu_items.append(
                ft.PopupMenuItem(
                    content=ft.Text(opt), 
                    on_click=lambda e, target_tf=text_field, val=opt: self.set_input_value(target_tf, val)
                )
            )
            
        # 3. Read extra database values if capability is implemented
        if allows_custom and hasattr(self.controller, "get_custom_options"):
            db_customs = self.controller.get_custom_options(category_name)
            if db_customs:
                for opt in db_customs:
                    menu_items.append(
                        ft.PopupMenuItem(
                            content=ft.Text(opt),
                            on_click=lambda e, target_tf=text_field, val=opt: self.set_input_value(target_tf, val)
                        )
                    )
                    
        popup_menu.items = menu_items
        
        # --- FIX: Intercept errors if the control hasn't been mounted to the page yet ---
        try:
            popup_menu.update()
        except RuntimeError:
            # Ignored during initial initialization; did_mount() handles synchronization later
            pass

    def set_input_value(self, target_text_field, value):
        target_text_field.value = value
        target_text_field.update()

    # --- POPUP TRIGGERS ---
    def show_delete_dialog(self, e):
        def action_delete():
            student_id = self.inputs["student_id"].value
            if hasattr(self.controller, "delete_student"):
                self.controller.delete_student(student_id)
            else:
                self.controller.show_dashboard()

        self.show_custom_popup(
            title="Delete profile?",
            message="Are you sure you want to irrevocably delete this student profile from the database?",
            on_confirm=action_delete,
            confirm_text="Yes, Delete"
        )

    def cancel_clicked(self, e, target_action=None):
        if target_action is None:
            target_action = self.controller.show_dashboard

        self.show_custom_popup(
            title="Unsaved changes",
            message="Are you sure you want to leave this view? Unsaved changes will be lost.",
            on_confirm=target_action,
            confirm_text="Yes, Discard"
        )

    def save_clicked(self, e):
        data = {k: v.value for k, v in self.inputs.items()}
        
        s_list_raw = self.inputs["sessions_list"].value
        if s_list_raw.strip():
            raw_entries = [s.strip() for s in s_list_raw.split(",") if s.strip()]
            data["sessions"] = [self.parse_to_iso_session(s) for s in raw_entries]
        else:
            data["sessions"] = []
            
        data["dob"] = self.inputs["dob"].value.strip()
        data["student_id"] = self.inputs["student_id"].value
        
        if "calculated_age" in data:
            del data["calculated_age"]
            
        self.controller.save_student(data)