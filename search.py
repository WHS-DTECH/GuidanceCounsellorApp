import flet as ft

class SearchView(ft.Container):
    def __init__(self, page: ft.Page, controller):
        super().__init__()
        self.main_page = page
        self.controller = controller
        self.expand = True
        self.bgcolor = "#F3F4F6"
        
        # Floating Action Button without icons
        self.main_page.floating_action_button = ft.FloatingActionButton(
            content=ft.Text("New Student", color="white"),
            bgcolor="#22C55E",
            width=140,
            shape=ft.RoundedRectangleBorder(radius=10),
            on_click=lambda _: self.controller.create_new_student_and_edit()
        )

        self.results_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)

        self.content = ft.Row(
            controls=[
                self.build_sidebar(),
                self.build_main_content(),
            ],
            spacing=0,
            expand=True
        )

    def did_mount(self):
        # Show button when view is loaded
        if self.main_page.floating_action_button:
            self.main_page.floating_action_button.visible = True
        self.main_page.update()
        self.refresh_list()

    def build_sidebar(self):
        return ft.Container(
            width=280,
            bgcolor="#1E293B",
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Text("SEND-C", size=28, weight="bold", color="white"),
                    ft.Divider(height=20, color="transparent"),
                    self.sidebar_item("DASHBOARD", on_click=lambda _: self.controller.cancel_session_and_go_back()),
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

    def build_main_content(self):
        return ft.Container(
            expand=True,
            padding=40,
            content=ft.Column(
                controls=[
                    ft.TextButton("< BACK", on_click=lambda _: self.controller.cancel_session_and_go_back()),
                    ft.Text("Student Database", size=32, weight="bold", color="#0F172A"),
                    ft.TextField(
                        hint_text="Search by name...",
                        on_change=self.on_search_change,
                    ),
                    self.results_list
                ]
            )
        )

    def refresh_list(self, search_term=""):
        self.results_list.controls.clear()
        students = self.controller.get_students()
        
        for s in students:
            # Check if full_name exists to avoid errors
            full_name = s.get("full_name", "")
            if search_term.lower() in full_name.lower():
                self.results_list.controls.append(
                    ft.Container(
                        content=ft.Text(f"{full_name} (ID: {s.get('student_id', 'N/A')})", color="black"),
                        padding=15, 
                        bgcolor="white", 
                        border_radius=10,
                        shadow=ft.BoxShadow(blur_radius=5, color="black12"),
                        on_click=lambda _, student=s: self.controller.show_editor(student)
                    )
                )
        self.update()

    def on_search_change(self, e):
        self.refresh_list(e.control.value)