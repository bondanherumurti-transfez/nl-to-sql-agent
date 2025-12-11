#!/usr/bin/env python3
"""
Setup script for NL to SQL Agent
Helps verify environment and configuration
"""

import os
import sys
from colorama import Fore, Style, init

init(autoreset=True)


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"{Fore.GREEN}✓ Python {version.major}.{version.minor}.{version.micro}{Style.RESET_ALL}")
        return True
    else:
        print(f"{Fore.RED}✗ Python 3.10+ required, found {version.major}.{version.minor}.{version.micro}{Style.RESET_ALL}")
        return False


def check_dependencies():
    """Check if dependencies are installed"""
    required = [
        'anthropic',
        'psycopg2',
        'dotenv',
        'tabulate',
        'colorama'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"{Fore.GREEN}✓ {package}{Style.RESET_ALL}")
        except ImportError:
            print(f"{Fore.RED}✗ {package}{Style.RESET_ALL}")
            missing.append(package)
    
    if missing:
        print(f"\n{Fore.YELLOW}Install missing packages:{Style.RESET_ALL}")
        print(f"pip install {' '.join(missing)}")
        return False
    return True


def check_env_file():
    """Check if .env file exists"""
    if os.path.exists('.env'):
        print(f"{Fore.GREEN}✓ .env file exists{Style.RESET_ALL}")
        return True
    else:
        print(f"{Fore.RED}✗ .env file not found{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Create .env from .env.example:{Style.RESET_ALL}")
        print("cp .env.example .env")
        return False


def check_env_variables():
    """Check if required environment variables are set"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'DB_HOST',
        'DB_PORT',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD',
        'ANTHROPIC_API_KEY'
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value and value != 'your_api_key_here':
            print(f"{Fore.GREEN}✓ {var}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ {var}{Style.RESET_ALL}")
            missing.append(var)
    
    if missing:
        print(f"\n{Fore.YELLOW}Set these variables in .env file:{Style.RESET_ALL}")
        for var in missing:
            print(f"  {var}=...")
        return False
    return True


def check_database_connection():
    """Check if database connection works"""
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers;")
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"{Fore.GREEN}✓ Database connection successful{Style.RESET_ALL}")
        print(f"{Fore.GREEN}  Found {count} customers{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}✗ Database connection failed: {e}{Style.RESET_ALL}")
        return False


def check_anthropic_api():
    """Check if Anthropic API key works"""
    try:
        from anthropic import Anthropic
        from dotenv import load_dotenv
        load_dotenv()
        
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        # Simple test call
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": "Say 'OK' if you can read this."
            }]
        )
        
        print(f"{Fore.GREEN}✓ Anthropic API connection successful{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}✗ Anthropic API connection failed: {e}{Style.RESET_ALL}")
        return False


def main():
    """Run all checks"""
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}NL to SQL Agent - Setup Verification{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        (".env File", check_env_file),
        ("Environment Variables", check_env_variables),
        ("Database Connection", check_database_connection),
        ("Anthropic API", check_anthropic_api),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{Fore.BLUE}Checking {name}...{Style.RESET_ALL}")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
            results.append((name, False))
    
    # Summary
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Setup Summary{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Fore.GREEN}✓" if result else f"{Fore.RED}✗"
        print(f"{status} {name}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}Passed: {passed}/{total}{Style.RESET_ALL}")
    
    if passed == total:
        print(f"\n{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}🎉 All checks passed! You're ready to go!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")
        print(f"{Fore.YELLOW}Run the agent:{Style.RESET_ALL}")
        print(f"  python agent.py\n")
        print(f"{Fore.YELLOW}Or run tests:{Style.RESET_ALL}")
        print(f"  python test_agent.py\n")
        return 0
    else:
        print(f"\n{Fore.RED}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.RED}Setup incomplete. Please fix the issues above.{Style.RESET_ALL}")
        print(f"{Fore.RED}{'='*80}{Style.RESET_ALL}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())