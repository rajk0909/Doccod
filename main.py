#Create By: Raj Karan
import os
import shutil
import threading
import subprocess
import asyncio
import re
import tkinter as tk
from tkinter import ttk
from ops import Ops


class FormApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("DoccoD")
        self.root.geometry("800x600")
        
        # Initialize Ops class for document generation
        self.ops = Ops()
        self.current_project_path = None
        
        # Top frame - Textbox and Load button
        top_frame = ttk.Frame(root, padding="10")
        top_frame.pack(fill=tk.X, side=tk.TOP)
        
        self.textbox = tk.Entry(top_frame, fg="gray")
        self.textbox.insert(0, "Enter Git url or Local codebase path to load")
        self.textbox.bind("<FocusIn>", self.on_textbox_focus_in)
        self.textbox.bind("<FocusOut>", self.on_textbox_focus_out)
        self.textbox.bind("<Return>", self.on_load_event)
        self.textbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.load_button = ttk.Button(top_frame, text="Load", command=self.on_load)
        self.load_button.pack(side=tk.LEFT, padx=5)
        
        # Progress bar frame, hidden until load starts
        self.cache_dir = os.path.join(os.getcwd(), "_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.progress_frame = ttk.Frame(root, padding="5")
        self.progress_label = ttk.Label(self.progress_frame, text="Loading project...")
        self.progress_label.pack(side=tk.LEFT, padx=(5, 10))
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode="determinate", length=300, maximum=100)
        self.progress_bar.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5)
        self.progress_percent_label = ttk.Label(self.progress_frame, text="0%", width=5)
        self.progress_percent_label.pack(side=tk.LEFT, padx=(5, 10))
        self.progress_frame.pack_forget()
        
        # Middle frame - Rich text box (70% of window)
        self.middle_frame = ttk.Frame(root, padding="10")
        self.middle_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        self.rich_text = tk.Text(self.middle_frame, wrap=tk.WORD, height=20)
        self.rich_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure text tags for formatting
        self.rich_text.tag_configure("center", justify=tk.CENTER)
        self.rich_text.tag_configure("bold", font=("Arial", 14, "bold"))
        self.rich_text.tag_configure("h1", font=("Arial", 18, "bold"), foreground="black")
        self.rich_text.tag_configure("h2", font=("Arial", 16, "bold"), foreground="black")
        self.rich_text.tag_configure("h3", font=("Arial", 14, "bold"), foreground="black")
        self.rich_text.tag_configure("text_bold", font=("Arial", 10, "bold"), foreground="black")
        self.rich_text.tag_configure("success", foreground="green")
        self.rich_text.tag_configure("failure", foreground="red")
        self.rich_text.tag_configure("document", foreground="black")
        
        # Insert welcome text
        self.rich_text.insert(tk.END, "Welcome to DoccoD", ("center", "bold"))
        self.rich_text.config(state=tk.DISABLED)
        
        # Bottom frame - Dropdown and Generate button
        bottom_frame = ttk.Frame(root, padding="10")
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.dropdown = ttk.Combobox(bottom_frame, values=["Starter Guide", "Project Architecture", "Dead Code Analysis"], state="readonly")
        self.dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.dropdown.current(0)
        
        self.generate_button = ttk.Button(bottom_frame, text="Generate", command=self.on_generate)
        self.generate_button.pack(side=tk.LEFT, padx=5)
        
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_load(self):
        """Handle Load button click"""
        source = self.textbox.get().strip()
        placeholder = "Enter Git url or Local codebase path to load"
        if source and source != placeholder:
            self.clear_welcome_text()
            self.disable_controls()
            self.show_progress()
            threading.Thread(target=self.load_project, args=(source,), daemon=True).start()
    
    def on_load_event(self, event):
        self.on_load()
        return "break"
    
    def on_textbox_focus_in(self, event):
        """Clear placeholder on focus"""
        if self.textbox.get() == "Enter Git url or Local codebase path to load":
            self.textbox.delete(0, tk.END)
            self.textbox.config(fg="black")
    
    def on_textbox_focus_out(self, event):
        """Restore placeholder if empty"""
        if self.textbox.get() == "":
            self.textbox.insert(0, "Enter Git url or Local codebase path to load")
            self.textbox.config(fg="gray")
    
    def on_generate(self):
        """Handle Generate button click"""
        if not self.current_project_path:
            self.log_message("Please load a project first before generating documentation.", "failure")
            return
        
        selected = self.dropdown.get()
        self.log_message(f"Generating {selected}...", "info")
        self.disable_controls()
        
        # Run generation in background thread
        threading.Thread(target=self.generate_documentation, args=(selected,), daemon=True).start()
    
    def generate_documentation(self, doc_type: str):
        """Generate documentation based on selected type"""
        try:
            # Run async function in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if doc_type == "Starter Guide":
                result = loop.run_until_complete(self.ops.starterguide(self.current_project_path))
            elif doc_type == "Project Architecture":
                result = loop.run_until_complete(self.ops.architecture_analysis(self.current_project_path))
            elif doc_type == "Dead Code Analysis":
                result = loop.run_until_complete(self.ops.dead_code_analysis(self.current_project_path))
            else:
                result = "Unknown documentation type."
            
            loop.close()
            
            # Display result with appropriate color
            if result.startswith("Error:"):
                self.root.after(0, self.log_message, result, "failure")
            else:
                self.root.after(0, self.log_message, result, "document")
        except Exception as e:
            self.root.after(0, self.log_message, f"Error generating {doc_type}: {str(e)}", "failure")
        finally:
            self.root.after(0, self.enable_controls)
    
    def on_closing(self):
        """Handle application closing - clear cache before exit"""
        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
        except Exception as e:
            print(f"Error clearing cache on exit: {e}")
        self.root.destroy()

    def clear_welcome_text(self):
        self.rich_text.config(state=tk.NORMAL)
        first_line = self.rich_text.get("1.0", "1.end")
        if first_line == "Welcome to DoccoD":
            self.rich_text.delete("1.0", "2.0")
        self.rich_text.config(state=tk.DISABLED)

    def show_progress(self):
        self.progress_frame.pack(fill=tk.X, side=tk.TOP, before=self.middle_frame)
        self.update_progress(0)

    def update_progress(self, value):
        """Update progress bar to specified percentage (0-100)"""
        self.progress_bar['value'] = value
        self.progress_percent_label.config(text=f"{value}%")
        self.root.update_idletasks()

    def finish_progress(self):
        self.update_progress(100)
        self.root.after(500, lambda: self.progress_frame.pack_forget())
        self.enable_controls()

    def disable_controls(self):
        self.load_button.config(state="disabled")
        self.generate_button.config(state="disabled")
        self.textbox.config(state="disabled")

    def enable_controls(self):
        self.load_button.config(state="normal")
        self.generate_button.config(state="normal")
        self.textbox.config(state="normal")

    def log_message(self, message, status="info"):
        """Log message to rich text box with markdown-like formatting. Status can be 'info', 'success', 'failure', or 'document'"""
        self.rich_text.config(state=tk.NORMAL)
        self.rich_text.delete("1.0", tk.END)  # Clear all previous text
        
        # Split by lines to handle headings
        lines = message.split('\n')
        
        for i, line in enumerate(lines):
            # Handle headings
            if line.startswith("### "):
                # H3 heading
                heading_text = line[4:]
                self.rich_text.insert(tk.END, heading_text + "\n", "h3")
            elif line.startswith("## "):
                # H3 heading
                heading_text = line[3:]
                self.rich_text.insert(tk.END, heading_text + "\n", "h3")
            elif line.startswith("# "):
                # H1 heading
                heading_text = line[2:]
                self.rich_text.insert(tk.END, heading_text + "\n", "h1")
            else:
                # Regular text with inline bold formatting
                self._insert_formatted_line(line)
                if i < len(lines) - 1:  # Add newline except for last line
                    self.rich_text.insert(tk.END, "\n")
        
        # Apply status color if needed
        if status == "failure":
            self.rich_text.tag_add("failure", "1.0", tk.END)
        
        self.rich_text.see(tk.END)
        self.rich_text.config(state=tk.DISABLED)
    
    def _insert_formatted_line(self, line):
        """Insert a line with bold formatting (**text** becomes bold)"""
        import re
        
        # Pattern to find **text** for bold
        pattern = r'\*\*([^*]+)\*\*'
        last_end = 0
        
        for match in re.finditer(pattern, line):
            # Insert text before the bold part
            if match.start() > last_end:
                self.rich_text.insert(tk.END, line[last_end:match.start()], "document")
            
            # Insert the bold text
            bold_text = match.group(1)
            self.rich_text.insert(tk.END, bold_text, "text_bold")
            last_end = match.end()
        
        # Insert remaining text
        if last_end < len(line):
            self.rich_text.insert(tk.END, line[last_end:], "document")
        
        # If no bold found, just insert the whole line
        elif last_end == 0:
            self.rich_text.insert(tk.END, line, "document")

    def is_git_url(self, source):
        lower = source.lower()
        return lower.startswith("http://") or lower.startswith("https://") or lower.startswith("git@")

    def sanitize_cache_name(self, source):
        safe = source.replace("/", "_").replace(":", "_").replace("@", "_").replace("?", "_").replace("=", "_")
        return safe[:120]
    
    def extract_project_name(self, source):
        """Extract a clean project name from source URL or path"""
        if self.is_git_url(source):
            # For git URLs, get the last part and remove .git extension
            project_name = source.rstrip("/").split("/")[-1]
            if project_name.lower().endswith(".git"):
                project_name = project_name[:-4]
        else:
            # For local paths, get the folder name
            project_name = os.path.basename(source.rstrip("\\"))
        return project_name

    def load_project(self, source):
        cache_name = self.sanitize_cache_name(source)
        cache_path = os.path.join(self.cache_dir, cache_name)
        project_name = self.extract_project_name(source)

        if self.is_git_url(source):
            self.root.after(0, self.log_message, f"Loading git repository into cache: {cache_path}", "info")
            self.root.after(0, self.update_progress, 10)
            try:
                if os.path.isdir(cache_path) and os.path.isdir(os.path.join(cache_path, ".git")):
                    self.root.after(0, self.update_progress, 25)
                    self.root.after(0, self.log_message, "Pulling latest changes from repository...", "info")
                    subprocess.check_output(["git", "-C", cache_path, "pull"], stderr=subprocess.STDOUT, text=True)
                else:
                    self.root.after(0, self.update_progress, 25)
                    if os.path.exists(cache_path):
                        self.root.after(0, self.log_message, "Removing old cache...", "info")
                        shutil.rmtree(cache_path)
                    self.root.after(0, self.update_progress, 50)
                    self.root.after(0, self.log_message, "Cloning repository...", "info")
                    subprocess.check_output(["git", "clone", source, cache_path], stderr=subprocess.STDOUT, text=True)
                self.root.after(0, self.update_progress, 90)
                self.root.after(0, self.log_message, f"✓ {project_name} Project loaded Successfully.", "success")
                self.current_project_path = cache_path
            except subprocess.CalledProcessError as exc:
                self.root.after(0, self.log_message, f"✗ Git load failed: {exc.output.strip()}", "failure")
        else:
            path = os.path.expanduser(source)
            if os.path.isdir(path):
                self.root.after(0, self.log_message, f"Copying local codebase into cache: {cache_path}", "info")
                self.root.after(0, self.update_progress, 25)
                try:
                    if os.path.exists(cache_path):
                        self.root.after(0, self.log_message, "Removing old cache...", "info")
                        shutil.rmtree(cache_path)
                    self.root.after(0, self.update_progress, 50)
                    self.root.after(0, self.log_message, "Copying project files...", "info")
                    shutil.copytree(path, cache_path)
                    self.root.after(0, self.update_progress, 90)
                    self.root.after(0, self.log_message, f"✓ {project_name} Project loaded Successfully.", "success")
                    self.current_project_path = cache_path
                except Exception as exc:
                    self.root.after(0, self.log_message, f"✗ Local copy failed: {exc}", "failure")
            else:
                self.root.after(0, self.log_message, f"✗ Invalid path: {path}", "failure")

        self.root.after(0, self.finish_progress)


if __name__ == "__main__":
    root = tk.Tk()
    app = FormApplication(root)
    root.mainloop()
