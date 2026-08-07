import flet as ft
from collections import Counter
import datetime

class DashboardView(ft.Container):
    def __init__(self, page: ft.Page, controller):
        super().__init__()
        self.main_page = page
        self.controller = controller
        self.expand = True
        self.bgcolor = "#F3F4F6"
        
        # UI Colors
        self.color_blue = "#3B82F6"
        self.color_accent = "#22C55E"
        self.color_orange = "orange"
        
        # Initialize filter variables
        self.selected_stat_type = "Gender"      
        self.selected_time_filter = "All Time"   
        self.selected_demographic = "All"        
        
        # Variables for the flexible timeline
        self.selected_timeline_mode = "Total Sessions" 
        self.selected_timeline_range = "Full Year"     
        
        # NEW: Variables for sub-filtering (Cross-comparison)
        self.selected_sub_filter = "All"
        self.sub_filter_dropdown_text = ft.Text("Filter: All ▾", color=self.color_blue, weight="bold")
        self.sub_filter_container = ft.Container()  # Holds the dropdown dynamically
        
        # NEW: Stores which groups in the legend are currently checked
        self.active_groups = set()
        # Remembers the last mode to detect when the mode has changed
        self.last_timeline_mode = "Total Sessions"
        
        # Placeholders for chart containers
        self.chart_container = ft.Container(expand=True)
        self.line_chart_container = ft.Container(expand=True)
        
        # Placeholders for dropdown texts to update visually
        self.stat_dropdown_text = ft.Text(f"{self.selected_stat_type} ▾", color=self.color_blue, weight="bold")
        self.time_dropdown_text = ft.Text(f"{self.selected_time_filter} ▾", color=self.color_blue, weight="bold")
        self.demo_dropdown_text = ft.Text(f"{self.selected_demographic} ▾", color=self.color_blue, weight="bold")
        self.mode_dropdown_text = ft.Text(f"{self.selected_timeline_mode} ▾", color=self.color_blue, weight="bold")
        self.range_dropdown_text = ft.Text(f"{self.selected_timeline_range} ▾", color=self.color_blue, weight="bold")
        
        # Build UI
        self.content = ft.Row(
            controls=[
                self.build_sidebar(),
                self.build_main_content(),
            ],
            spacing=0,
            expand=True
        )

    def build_sidebar(self):
        return ft.Container(
            width=280,
            bgcolor="#1E293B",
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text("SEND-C", size=28, weight="bold", color="white"),
                        margin=ft.Margin(0, 0, 0, 40)
                    ),
                    self.sidebar_item("DASHBOARD", active=True),
                    self.sidebar_item("STUDENTS", on_click=lambda _: self.controller.go_to_search()),
                    ft.VerticalDivider(expand=True, color="transparent"),
                    ft.ElevatedButton(
                        "NEW SESSION",
                        color="white",
                        bgcolor=self.color_accent,
                        on_click=lambda _: self.controller.start_new_session()
                    )
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
        self.update_charts_logic()

        return ft.Container(
            expand=True,
            padding=40,
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Row([
                        ft.Text("Overview & Analytics", size=32, weight="bold", color="#0F172A"),
                    ], alignment="spaceBetween"),
                    
                    ft.Divider(height=20, color="transparent"),
                    
                    ft.Row([
                        self.stat_card("Total Registered Students", str(len(self.controller.get_students())), self.color_blue),
                        self.stat_card("Total Sessions Logged", str(self.get_total_sessions_count()), self.color_accent),
                    ], spacing=20),
                    
                    ft.Divider(height=20, color="transparent"),
                    
                    # --- CHARTS ROW ---
                    ft.Row([
                        # Left Box: Distribution Profiles
                        ft.Container(
                            expand=True,
                            bgcolor="white",
                            padding=20,
                            border_radius=15,
                            height=450,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text("Distribution Profiles", size=18, weight="bold"),
                                    self.create_dropdown(["Gender", "Ethnicity", "Referral Type"], self.stat_dropdown_text, self.on_stat_type_change),
                                ], alignment="spaceBetween"),
                                ft.Divider(height=10, color="transparent"),
                                self.chart_container
                            ])
                        ),
                        # Right Box: Session Tracking Timeline
                        ft.Container(
                            expand=True,
                            bgcolor="white",
                            padding=20,
                            border_radius=15,
                            content=ft.Column([
                                ft.Column([
                                    ft.Text("Session Tracking Timeline", size=18, weight="bold"),
                                    ft.Divider(height=5, color="transparent"),
                                    ft.Row([
                                        self.create_dropdown(["Total Sessions", "Compare Gender", "Compare Ethnicity", "Compare Age", "Compare Referral Type"], self.mode_dropdown_text, self.on_timeline_mode_change),
                                        self.create_dropdown(["Full Year", "Last 6 Months", "Last 30 Days"], self.range_dropdown_text, self.on_timeline_range_change),
                                        self.sub_filter_container,  # Dynamic sub-filter dropdown
                                    ], spacing=5, wrap=True)
                                ]),
                                ft.Divider(height=15, color="transparent"),
                                self.line_chart_container
                            ])
                        )
                    ], spacing=20, vertical_alignment="start")
                ]
            )
        )

    def stat_card(self, title, value, color):
        return ft.Container(
            expand=True,
            bgcolor="white",
            border_radius=15,
            padding=20,
            content=ft.Column([
                ft.Text(title, color="grey", size=12),
                ft.Text(value, size=30, weight="bold", color=color),
            ])
        )

    def create_dropdown(self, options_list, text_control, on_change_func):
        menu_items = []
        for opt in options_list:
            menu_items.append(
                ft.PopupMenuItem(
                    content=ft.Text(opt),
                    on_click=lambda e, val=opt: on_change_func(val)
                )
            )
        return ft.PopupMenuButton(
            items=menu_items,
            content=ft.Container(
                content=text_control,
                padding=8,
                border=ft.Border(
                    top=ft.BorderSide(1, "#CBD5E1"),
                    bottom=ft.BorderSide(1, "#CBD5E1"),
                    left=ft.BorderSide(1, "#CBD5E1"),
                    right=ft.BorderSide(1, "#CBD5E1")
                ),
                border_radius=8
            )
        )

    # --- FILTER CALLBACKS ---
    def on_stat_type_change(self, val):
        self.selected_stat_type = val
        self.stat_dropdown_text.value = f"{val} ▾"
        self.update_charts_logic()
        self.main_page.update()

    def on_timeline_mode_change(self, val):
        self.selected_timeline_mode = val
        self.mode_dropdown_text.value = f"{val} ▾"
        # Reset sub-filter when mode changes
        self.selected_sub_filter = "All"
        self.sub_filter_dropdown_text.value = "Filter: All ▾"
        self.update_charts_logic()
        self.main_page.update()

    def on_timeline_range_change(self, val):
        self.selected_timeline_range = val
        self.range_dropdown_text.value = f"{val} ▾"
        self.update_charts_logic()
        self.main_page.update()

    def on_sub_filter_change(self, val):
        self.selected_sub_filter = val
        self.sub_filter_dropdown_text.value = f"Filter: {val.split(': ')[-1] if ':' in val else val} ▾"
        self.update_charts_logic()
        self.main_page.update()

    def on_legend_checkbox_change(self, e, group_name):
        if e.control.value:
            self.active_groups.add(group_name)
        else:
            self.active_groups.discard(group_name)
        self.update_charts_logic()
        self.main_page.update()

    def get_total_sessions_count(self):
        return sum(len(s.get("sessions", [])) for s in self.controller.get_students())

    # --- DYNAMIC OPTIONS GENERATION ---
    def update_sub_filter_dropdown(self, students):
        """Generates sub-filter options ONLY when 'Compare Referral Type' is active."""
        if self.selected_timeline_mode != "Compare Referral Type":
            self.sub_filter_container.content = None
            self.selected_sub_filter = "All"
            return

        # Dynamically collect all variants from genuine student data
        genders = set(str(s.get("gender", "")).strip() for s in students if s.get("gender"))
        ethnicities = set(str(s.get("ethnicity", "")).strip() for s in students if s.get("ethnicity"))
        
        options = ["All"]
        for g in sorted(genders):
            if g: options.append(f"Gender: {g}")
        for e in sorted(ethnicities):
            if e: options.append(f"Ethnicity: {e}")

        # Validate selection
        if self.selected_sub_filter != "All" and self.selected_sub_filter not in options:
            self.selected_sub_filter = "All"
            self.sub_filter_dropdown_text.value = "Filter: All ▾"

        self.sub_filter_container.content = self.create_dropdown(
            options, 
            self.sub_filter_dropdown_text, 
            self.on_sub_filter_change
        )

    def update_charts_logic(self):
        students = self.controller.get_students()
        now = datetime.datetime.now()
        
        # Check and load sub-filter visibility
        self.update_sub_filter_dropdown(students)
        
        # 1. MAIN FILTERING (Left)
        filtered_students = []
        for s in students:
            if self.selected_time_filter == "This Month":
                has_session_this_month = any(t.startswith(now.strftime("%Y-%m")) for t in s.get("sessions", []))
                if has_session_this_month: filtered_students.append(s)
            elif self.selected_time_filter == "This Year":
                has_session_this_year = any(t.startswith(now.strftime("%Y")) for t in s.get("sessions", []))
                if has_session_this_year: filtered_students.append(s)
            else:
                filtered_students.append(s)

        # 2. BAR CHART LEFT (Distributions)
        key_map = {"Gender": "gender", "Ethnicity": "ethnicity", "Referral Type": "referral_type"}
        db_key = key_map[self.selected_stat_type]
        
        raw_values = []
        for s in filtered_students:
            val = s.get(db_key)
            if val is not None and str(val).strip() != "":
                raw_values.append(str(val).strip())
                
        counts = Counter(raw_values)
        total_counts = sum(counts.values())

        chart_rows = []
        if total_counts > 0:
            for label, count in counts.items():
                percentage = count / total_counts
                chart_rows.append(
                    ft.Column([
                        ft.Row([
                            ft.Text(label, weight="w500", size=14, expand=True),
                            ft.Text(f"{count}x ({int(percentage*100)}%)", size=12, color="grey")
                        ]),
                        ft.Container(
                            content=ft.Row([
                                ft.Container(bgcolor=self.color_blue, expand=int(percentage*100) if percentage > 0 else 1, height=12, border_radius=6),
                                ft.Container(bgcolor="#E2E8F0", expand=100 - int(percentage*100) if percentage < 1 else 0, height=12, border_radius=6)
                            ], spacing=0),
                            border_radius=6
                        ),
                        ft.Divider(height=10, color="transparent")
                    ])
                )
            self.chart_container.content = ft.Column(controls=chart_rows, scroll=ft.ScrollMode.AUTO)
        else:
            self.chart_container.content = ft.Text("No data available for this filter combination.", color="grey")

        # 3. DYNAMIC TIMELINE LOGIC (Right)
        timeline_slots = []
        labels_list = []
        
        if self.selected_timeline_range == "Last 30 Days":
            for i in range(29, -1, -1):
                d = now - datetime.timedelta(days=i)
                timeline_slots.append(d.strftime("%Y-%m-%d"))
            labels_list = [t[8:] if idx % 5 == 0 else "" for idx, t in enumerate(timeline_slots)]
        elif self.selected_timeline_range == "Last 6 Months":
            for i in range(5, -1, -1):
                target_date = now - datetime.timedelta(days=i*30)
                timeline_slots.append(target_date.strftime("%Y-%m"))
            months_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            labels_list = [months_names[int(t[5:])-1] for t in timeline_slots]
        else: # Full Year
            for m in range(1, 13):
                timeline_slots.append(f"{now.year}-{m:02d}")
            labels_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        color_palette = ["#3B82F6", "#EC4899", "#22C55E", "#F59E0B", "#A855F7", "#64748B", "#14B8A6", "#EF4444", "#06B6D4"]
        
        compare_key = None
        if "Gender" in self.selected_timeline_mode: compare_key = "gender"
        elif "Ethnicity" in self.selected_timeline_mode: compare_key = "ethnicity"
        elif "Age" in self.selected_timeline_mode: compare_key = "age"
        elif "Referral Type" in self.selected_timeline_mode: compare_key = "referral_type"

        # Determine all existing groups
        all_possible_groups = set()
        if compare_key:
            for s in students:
                val = s.get(compare_key)
                if val is not None and str(val).strip() != "":
                    all_possible_groups.add(str(val).strip())
        all_possible_groups = sorted(list(all_possible_groups))

        # If the main mode has changed, initialize all groups as active (checked)
        if self.selected_timeline_mode != self.last_timeline_mode:
            self.active_groups = set(all_possible_groups)
            self.last_timeline_mode = self.selected_timeline_mode

        group_colors = {group: color_palette[i % len(color_palette)] for i, group in enumerate(all_possible_groups)}

        counts_tracked = {slot: 0 for slot in timeline_slots}
        group_counts_tracked = {slot: {group: 0 for group in all_possible_groups} for slot in timeline_slots}

        for s in students:
            # === SUB-FILTER LOGIC (ONLY ACTIVE FOR COMPARE REFERRAL TYPE) ===
            if self.selected_timeline_mode == "Compare Referral Type" and self.selected_sub_filter != "All":
                attr_type, attr_val = self.selected_sub_filter.split(": ")
                student_val = str(s.get(attr_type.lower(), "")).strip()
                if student_val != attr_val:
                    continue  # Skip students who do not match the filter criteria

            group_val = s.get(compare_key)
            if compare_key:
                if group_val is None or str(group_val).strip() == "":
                    continue
                group_val = str(group_val).strip()

            for session_time in s.get("sessions", []):
                if not session_time: continue
                
                match_key = None
                if self.selected_timeline_range == "Last 30 Days" and len(session_time) >= 10:
                    match_key = session_time[:10]
                elif len(session_time) >= 7:
                    match_key = session_time[:7]
                    
                if match_key in counts_tracked:
                    counts_tracked[match_key] += 1
                    if compare_key and group_val in group_counts_tracked[match_key]:
                        group_counts_tracked[match_key][group_val] += 1

        # Calculate max value for scaling (considering only active groups)
        all_vals = [0]
        if compare_key:
            for slot in timeline_slots:
                for group in all_possible_groups:
                    if group in self.active_groups:
                        all_vals.append(group_counts_tracked[slot][group])
        else:
            all_vals.extend(counts_tracked.values())
        max_val = max(all_vals) if max(all_vals) > 0 else 1

        timeline_bars = []
        for idx, slot in enumerate(timeline_slots):
            if compare_key:
                sub_bars = []
                base_width = 14 if self.selected_timeline_range == "Last 30 Days" else 24
                
                active_groups_count = len(self.active_groups)
                bar_width = max(int(base_width / active_groups_count), 3) if active_groups_count else 4
                
                for group in all_possible_groups:
                    if group in self.active_groups:
                        g_count = group_counts_tracked[slot][group]
                        h_group = (g_count / max_val) * 140
                        sub_bars.append(
                            ft.Container(
                                bgcolor=group_colors[group],
                                width=bar_width,
                                height=max(h_group, 2),
                                border_radius=1,
                                tooltip=f"{group}: {g_count} Sessions"
                            )
                        )
                bar_content = ft.Row(controls=sub_bars, alignment="end", spacing=1)
            else:
                h_total = (counts_tracked[slot] / max_val) * 140
                display_date = slot
                if self.selected_timeline_range == "Last 30 Days":
                    try:
                        parsed_d = datetime.datetime.strptime(slot, "%Y-%m-%d")
                        display_date = parsed_d.strftime("%d.%m.")
                    except: pass

                bar_content = ft.Container(
                    bgcolor=self.color_accent if counts_tracked[slot] > 0 else "#E2E8F0",
                    width=14,
                    height=max(h_total, 4),
                    border_radius=4,
                    tooltip=f"{display_date}: {counts_tracked[slot]} Sessions"
                )

            timeline_bars.append(
                ft.Column([
                    ft.Container(
                        height=150,
                        content=ft.Column([ft.Container(expand=True), bar_content], alignment="end")
                    ),
                    ft.Text(labels_list[idx], size=9, weight="bold", color="#64748B")
                ], alignment="center", horizontal_alignment="center")
            )

        # Build legend
        if compare_key:
            legend_widgets = []
            for group in all_possible_groups:
                legend_widgets.append(
                    ft.Row([
                        ft.Container(bgcolor=group_colors[group], width=12, height=12, border_radius=3),
                        ft.Checkbox(
                            label=group,
                            value=group in self.active_groups,
                            label_style=ft.TextStyle(size=12),
                            on_change=lambda e, g=group: self.on_legend_checkbox_change(e, g)
                        )
                    ], spacing=4)
                )
            
            self.line_chart_container.content = ft.Column([
                ft.Container(
                    content=ft.Row(controls=timeline_bars, alignment="spaceEvenly", vertical_alignment="end", scroll=ft.ScrollMode.ADAPTIVE),
                    expand=True
                ),
                ft.Divider(height=15, color="transparent"),
                ft.Row(controls=legend_widgets, alignment="center", spacing=15, wrap=True)
            ], expand=True)
        else:
            self.line_chart_container.content = ft.Row(
                controls=timeline_bars,
                alignment="spaceEvenly",
                vertical_alignment="end",
                scroll=ft.ScrollMode.ADAPTIVE
            )