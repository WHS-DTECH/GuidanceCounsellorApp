import flet as ft


class LoginView(ft.Container):
    def __init__(self, page: ft.Page, controller, is_registration=False):
        super().__init__()
        self.main_page = page
        self.controller = controller
        self.is_registration = is_registration

        self.expand = True
        self.bgcolor = "#F3F4F6"

        self.username_input = ft.TextField(label="Username", autofocus=True)
        self.password_input = ft.TextField(label="Password", password=True, can_reveal_password=True)
        self.message_text = ft.Text("", color="#EF4444", size=13)

        self.content = ft.Row(
            alignment="center",
            vertical_alignment="center",
            controls=[
                ft.Container(
                    width=420,
                    bgcolor="white",
                    border_radius=16,
                    padding=30,
                    shadow=ft.BoxShadow(blur_radius=12, color="black12"),
                    content=ft.Column(
                        tight=True,
                        controls=[
                            ft.Text("SEND-C", size=32, weight="bold", color="#0F172A"),
                            ft.Text(
                                "Create an account" if self.is_registration else "Sign in",
                                size=16,
                                color="#475569",
                            ),
                            ft.Divider(height=12, color="transparent"),
                            self.username_input,
                            self.password_input,
                            self.message_text,
                            ft.Divider(height=6, color="transparent"),
                            ft.ElevatedButton(
                                "Create account" if self.is_registration else "Login",
                                bgcolor="#22C55E",
                                color="white",
                                height=44,
                                on_click=self.submit,
                            ),
                            ft.OutlinedButton(
                                "Continue with Google",
                                icon=ft.icons.GOOGLE,
                                height=44,
                                on_click=self.google_login,
                            ),
                        ],
                    ),
                )
            ],
        )

    def submit(self, _):
        username = (self.username_input.value or "").strip()
        password = (self.password_input.value or "").strip()

        if not username or not password:
            self.message_text.value = "Username and password are required."
            self.update()
            return

        if self.is_registration:
            self.controller.register_new_user(username, password)
            return

        if self.controller.verify_login(username, password):
            self.controller.login_success()
            return

        self.message_text.value = "Invalid username or password."
        self.update()

    def google_login(self, _):
        self.controller.google_auth.start_login()

    def set_message(self, message):
        self.message_text.value = message
        self.update()
