import json
import os
import sys
import keyring
from pathlib import Path
from rich.console import Console

console = Console()

# Path where the configuration will be saved (~/.diatax_config.json)
CONFIG_FILE = Path.home() / ".diatax_config.json"
SERVICE_NAME = "diatax"

def save_config(provider: str, model: str, api_key: str, output_language: str = "english"):
    """
    Saves general configuration in JSON and API Key in system Keyring.
    Implements Fail-Secure policy: if the vault fails, nothing is saved.
    """
    config_data = {
        "provider": provider,
        "model": model,
        "output_language": output_language
    }

    # 1. Save API Key in system vault (FAIL-SECURE)
    try:
        keyring.set_password(SERVICE_NAME, "api_key", api_key)
    except Exception as e:
        console.print(f"[bold red]❌ Critical security error: System keyring is not available. "
                      f"For your protection, the API Key will not be saved in plain text.[/bold red]")
        sys.exit(1)

    # 2. Save the rest in the JSON file
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
    except (PermissionError, OSError) as e:
        console.print(f"[bold red]❌ System error: Could not write configuration file. "
                      f"Detail: {str(e)}[/bold red]")
        sys.exit(1)

def load_config():
    """
    Reads general configuration and retrieves API Key from Keyring.
    Distinguishes between normal states and critical system failures.
    """
    try:
        if not CONFIG_FILE.exists():
            return {}

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        # Retrieve the key from the vault
        api_key = keyring.get_password(SERVICE_NAME, "api_key")
        
        if api_key:
            config_data["api_key"] = api_key
            
            # Export to environment for LiteLLM
            provider = config_data.get("provider", "").lower()
            if "gemini" in provider:
                os.environ["GEMINI_API_KEY"] = api_key
            elif "openai" in provider:
                os.environ["OPENAI_API_KEY"] = api_key
            elif "groq" in provider:
                os.environ["GROQ_API_KEY"] = api_key
            elif "anthropic" in provider:
                os.environ["ANTHROPIC_API_KEY"] = api_key

        return config_data

    except Exception as e:
        console.print(f"[bold red]⚠ Error loading configuration: {str(e)}[/bold red]")
        return {}
