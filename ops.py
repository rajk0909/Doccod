import os
import asyncio
from typing import Optional
from copilot import CopilotClient


class Ops:
    """Operations class for handling DoccoD documentation generation via GitHub Copilot SDK"""
    
    def __init__(self):
        """Initialize Ops class"""
        self.model = "gpt-4.1"  # Specify the model to use for Copilot
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            print("Warning: GITHUB_TOKEN environment variable not set. Authentication may fail.")
            print("Set it with: $env:GITHUB_TOKEN = 'your_github_token'")

    
    def _read_project_files(self, project_path: str, max_files: int = 50) -> dict:
        """
        Read relevant project files to understand the codebase
        
        Args:
            project_path: Path to the cached project
            max_files: Maximum number of files to read
            
        Returns:
            Dictionary containing file contents
        """
        file_contents = {}
        file_count = 0
        
        # Important file patterns to look for
        important_files = [
            "README.md", "package.json", "requirements.txt", 
            "setup.py", ".gitignore", "Dockerfile"
        ]
        
        # File extensions and names to ignore
        ignore_extensions = ('.mf', '.jpg', '.png', '.class', '.jar', '.properties', '.form')
        ignore_files = {'LICENSE'}
        
        try:
            # First, collect important files
            for root, dirs, files in os.walk(project_path):
                # Skip common directories
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv', 'venv']]
                
                for file in files:
                    if file_count >= max_files:
                        break
                    
                    # Skip ignored files and extensions
                    if file in ignore_files or file.endswith(ignore_extensions):
                        continue
                    
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, project_path)
                    
                    # Prioritize important files
                    if file in important_files or file.endswith(('.py', '.js', '.ts', '.java', '.go', '.md')):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read(5000)  # Read first 5000 chars
                                file_contents[rel_path] = content
                                file_count += 1
                        except Exception as e:
                            print(f"Error reading {rel_path}: {e}")
                
                if file_count >= max_files:
                    break
        
        except Exception as e:
            print(f"Error reading project files: {e}")
        
        return file_contents
    
    def _prepare_project_context(self, file_contents: dict, project_path: str) -> str:
        """
        Prepare project context from file contents
        
        Args:
            file_contents: Dictionary of file contents
            project_path: Path to the project
            
        Returns:
            Formatted project context string
        """
        context = f"Project: {os.path.basename(project_path)}\n\n"
        context += "Files analyzed:\n"
        
        for file_path, content in file_contents.items():
            context += f"\n--- {file_path} ---\n"
            context += content[:1000]  # Include first 1000 chars of each file
            if len(content) > 1000:
                context += "\n... (truncated)"
        
        return context
    
    async def _on_permission_request(self, permission):
        """
        Handle permission requests from Copilot SDK
        """
        return True  # Auto-approve permissions
    
    async def _call_copilot(self, prompt: str) -> str:
        """
        Call GitHub Copilot SDK with the given prompt
        
        Args:
            prompt: The prompt to send to Copilot
            
        Returns:
            Response from Copilot
        """
        try:
            # Initialize client - SDK will use GITHUB_TOKEN env var or system auth
            client = CopilotClient()
            async with client:
                session = await client.create_session(
                    model=self.model,
                    on_permission_request=self._on_permission_request
                )
                response = await session.send_and_wait(prompt)
                return response.data.content
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "not created with authentication" in error_msg.lower():
                return f"Error: Authentication failed. Please set GITHUB_TOKEN environment variable:\n$env:GITHUB_TOKEN = 'your_github_token'"
            return f"Error: {error_msg}"
    
    async def starterguide(self, project_path: str) -> str:
        """
        Generate a Starter Guide for the cached project using GitHub Copilot SDK
        
        Args:
            project_path: Path to the cached project directory
            
        Returns:
            Generated Starter Guide content
        """
        if not os.path.isdir(project_path):
            return f"Error: Project path '{project_path}' does not exist or is not a directory."
        
        try:
            # Read project files
            print(f"Reading project files from {project_path}...")
            file_contents = self._read_project_files(project_path)
            
            if not file_contents:
                return "Error: No project files found to analyze."
            
            # Prepare the prompt for Copilot
            project_context = self._prepare_project_context(file_contents, project_path)
            
            prompt = f"""You are an expert technical writer. Based on the following project structure and code samples, 
generate a comprehensive Starter Guide that helps new developers understand and get started with this project.

PROJECT STRUCTURE:
{project_context}

Please generate a Starter Guide with the following sections:
1. Project Overview - Brief description of what the project does
2. Prerequisites - Required tools and dependencies
3. Installation - Step-by-step setup instructions
4. Quick Start - How to get the project running quickly
5. Project Structure - Overview of key directories and files
6. Configuration - How to configure the project
7. Common Tasks - How to perform common development tasks
8. Troubleshooting - Common issues and solutions

Make the guide clear, concise, and suitable for new team members."""
            
            # Call Copilot API
            print("Generating Starter Guide with Copilot...")
            starter_guide = await self._call_copilot(prompt)
            return starter_guide
        
        except Exception as e:
            return f"Error generating Starter Guide: {str(e)}"
    
    async def architecture_analysis(self, project_path: str) -> str:
        """
        Generate a Project Architecture analysis using GitHub Copilot SDK
        
        Args:
            project_path: Path to the cached project directory
            
        Returns:
            Generated Architecture Analysis
        """
        if not os.path.isdir(project_path):
            return f"Error: Project path does not exist."
        
        try:
            file_contents = self._read_project_files(project_path)
            project_context = self._prepare_project_context(file_contents, project_path)
            
            prompt = f"""Based on the following project structure and code, provide a detailed Project Architecture analysis:

{project_context}

Please include:
1. High-level architecture overview
2. Key components and their responsibilities
3. Data flow and interactions
4. Technology stack
5. Design patterns used
6. Scalability considerations
7. Dependencies and external services"""
            
            print("Generating Architecture Analysis with Copilot...")
            result = await self._call_copilot(prompt)
            return result
        
        except Exception as e:
            return f"Error generating Architecture Analysis: {str(e)}"
    
    async def dead_code_analysis(self, project_path: str) -> str:
        """
        Generate a Dead Code Analysis using GitHub Copilot SDK
        
        Args:
            project_path: Path to the cached project directory
            
        Returns:
            Generated Dead Code Analysis
        """
        if not os.path.isdir(project_path):
            return f"Error: Project path does not exist."
        
        try:
            file_contents = self._read_project_files(project_path)
            project_context = self._prepare_project_context(file_contents, project_path)
            
            prompt = f"""Analyze the following project code and identify potential dead code:

{project_context}

Please identify and report:
1. Unused functions or methods
2. Unused imports or dependencies
3. Unreachable code blocks
4. Unused variables
5. Dead exports or public APIs
6. Deprecated code still in use
7. Recommendations for cleanup

For each finding, include the file path, line context, and severity level."""
            
            print("Generating Dead Code Analysis with Copilot...")
            result = await self._call_copilot(prompt)
            return result
        
        except Exception as e:
            return f"Error generating Dead Code Analysis: {str(e)}"
