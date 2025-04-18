#!/usr/bin/env python
"""
Setup script for Kwizify API.

This script helps with initial setup of the project including:
1. Creating a virtual environment
2. Installing dependencies
3. Setting up the database
4. Creating a sample admin user

Usage:
    python setup.py
"""

import os
import subprocess
import sys
import time
from getpass import getpass
import argparse


def run_command(command, description=None):
    """Run a shell command and print its status."""
    if description:
        print(f"\n{description}...")

    try:
        subprocess.run(command, check=True, shell=True)
        if description:
            print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        if description:
            print(f"❌ {description} failed")
        print(f"Error: {e}")
        return False


def create_venv():
    """Create and activate a virtual environment."""
    if os.path.exists(".venv"):
        print("Virtual environment already exists.")
        return True

    if not run_command("python -m venv .venv", "Creating virtual environment"):
        return False

    # Activate virtual environment (this doesn't work directly here but provides instructions)
    if sys.platform == "win32":
        print("\nTo activate the virtual environment, run:")
        print(".\.venv\\Scripts\\activate")
    else:
        print("\nTo activate the virtual environment, run:")
        print("source .venv/bin/activate")

    return True


def install_dependencies():
    """Install project dependencies."""
    if sys.platform == "win32":
        pip_path = ".\.venv\\Scripts\\pip"
    else:
        pip_path = "./.venv/bin/pip"

    return run_command(f"{pip_path} install -r requirements.txt", "Installing dependencies")


def setup_database():
    """Set up the database with Alembic."""
    if sys.platform == "win32":
        alembic_path = ".\.venv\\Scripts\\alembic"
    else:
        alembic_path = "./.venv/bin/alembic"

    return run_command(f"{alembic_path} upgrade head", "Setting up database with Alembic")


def download_spacy_model():
    """Download the spaCy language model."""
    if sys.platform == "win32":
        python_path = ".\.venv\\Scripts\\python"
    else:
        python_path = "./.venv/bin/python"

    return run_command(f"{python_path} -m spacy download en_core_web_sm", "Downloading spaCy language model")


def create_env_file():
    """Create a .env file if it doesn't exist."""
    if os.path.exists(".env"):
        print(".env file already exists.")
        return True

    try:
        with open(".env.example", "r") as example_file:
            example_content = example_file.read()

        print("\nCreating .env file from template...")
        print("Please provide the following configuration values:")

        db_url = input("Database URL (default: postgresql://postgres:password@localhost:5432/kwizify): ")
        if not db_url:
            db_url = "postgresql://postgres:password@localhost:5432/kwizify"

        google_api_key = input("Google API Key (or press Enter to skip for now): ")

        jwt_secret = input("JWT Secret Key (default: a-secure-jwt-secret-key-change-in-production): ")
        if not jwt_secret:
            jwt_secret = "a-secure-jwt-secret-key-change-in-production"

        content = example_content
        content = content.replace("postgresql://postgres:password@localhost:5432/kwizify", db_url)
        content = content.replace("your-google-api-key", google_api_key or "your-google-api-key")
        content = content.replace("your-secret-key-change-in-production", jwt_secret)

        with open(".env", "w") as env_file:
            env_file.write(content)

        print("✅ .env file created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def main():
    """Run the setup process."""
    parser = argparse.ArgumentParser(description="Setup script for Kwizify API")
    parser.add_argument("--skip-venv", action="store_true", help="Skip virtual environment creation")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependencies installation")
    args = parser.parse_args()

    print("====== Kwizify API Setup ======")

    # Create virtual environment
    if not args.skip_venv:
        if not create_venv():
            print("Failed to create virtual environment. Exiting...")
            return

    # Create .env file
    if not create_env_file():
        print("Failed to create .env file. Exiting...")
        return

    # Continue with installation if not skipped
    if not args.skip_deps:
        print("\n⚠️ Please make sure you've activated the virtual environment!")
        proceed = input("Continue with installation? (y/n): ").lower()
        if proceed != 'y':
            print("Setup aborted.")
            return

        if not install_dependencies():
            print("Failed to install dependencies. Exiting...")
            return

        if not download_spacy_model():
            print("Failed to download spaCy model. Exiting...")
            return

        if not setup_database():
            print("Failed to set up database. Exiting...")
            return

    print("\n🎉 Setup completed successfully!")
    print("\nTo start the development server:")
    print("1. Make sure your virtual environment is activated")
    print("2. Run: python main.py")


if __name__ == "__main__":
    main()