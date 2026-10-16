"""Pytest configuration: load backend/.env so integration tests can detect credentials."""
from dotenv import load_dotenv

load_dotenv()
