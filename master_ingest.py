#!/usr/bin/env python3
"""
Master MFS Ingestion Script
Choose and run the best ingestion method for your needs
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """Print welcome banner"""
    print("=" * 60)
    print("🚀 MFS RAG Master Ingestion System")
    print("=" * 60)
    print()

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking Environment...")
    
    required_env_vars = [
        'OPENAI_API_KEY',
        'POSTGRES_HOST',
        'POSTGRES_DB',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("💡 Make sure to set these in your .env file")
        return False
    
    # Optional but recommended
    confluence_vars = ['CONFLUENCE_USERNAME', 'CONFLUENCE_API_TOKEN']
    confluence_configured = all(os.getenv(var) for var in confluence_vars)
    
    print("✅ Required environment variables found")
    if confluence_configured:
        print("✅ Confluence authentication configured")
    else:
        print("⚠️ Confluence authentication not configured (may limit access)")
    
    return True

def check_docker_network():
    """Check if Docker network is running"""
    print("\n🐳 Checking Docker Network...")
    try:
        result = subprocess.run(
            ["docker", "network", "ls"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        if "rag_rag-network" in result.stdout:
            print("✅ Docker network rag_rag-network found")
            return True
        else:
            print("⚠️ Docker network rag_rag-network not found")
            print("💡 Start your RAG system first:")
            print("   docker-compose -f docker-compose-openai-working.yml up -d")
            return False
    except subprocess.CalledProcessError:
        print("❌ Docker not available or not running")
        return False

def show_ingestion_options():
    """Display available ingestion options"""
    print("\n📋 Available Ingestion Methods:")
    print()
    
    options = [
        {
            'num': '1',
            'name': 'Docling Enhanced (Recommended)',
            'file': 'ingest_docling_simple.py',
            'description': 'Advanced document analysis with table extraction',
            'pros': ['Structured content processing', 'Table extraction', 'Best for complex documents'],
            'cons': ['Requires Docling installation', 'Slightly slower']
        },
        {
            'num': '2', 
            'name': 'Standalone Fixed (Reliable)',
            'file': 'ingest_standalone_fixed.py',
            'description': 'Direct API approach with enhanced error handling',
            'pros': ['Most reliable', 'Direct OpenAI API', 'Good error handling'],
            'cons': ['No advanced document structure']
        },
        {
            'num': '3',
            'name': 'Standalone Basic',
            'file': 'ingest_standalone.py', 
            'description': 'Simple ingestion for quick setup',
            'pros': ['Fast and simple', 'Minimal dependencies'],
            'cons': ['Basic functionality only']
        },
        {
            'num': '4',
            'name': 'Run All Methods',
            'file': 'all',
            'description': 'Run all ingestion methods in sequence',
            'pros': ['Comprehensive coverage', 'Multiple processing approaches'],
            'cons': ['Takes longest time', 'May create duplicate content']
        }
    ]
    
    for option in options:
        print(f"🎯 [{option['num']}] {option['name']}")
        print(f"   File: {option['file']}")
        print(f"   {option['description']}")
        print(f"   ✅ Pros: {', '.join(option['pros'])}")
        print(f"   ⚠️ Cons: {', '.join(option['cons'])}")
        print()
    
    return options

def run_docker_ingestion(script_name: str, method_name: str):
    """Run ingestion script in Docker container"""
    print(f"\n🚀 Running {method_name}...")
    print(f"📄 Script: {script_name}")
    print("-" * 40)
    
    # Determine required packages based on script
    if 'docling' in script_name:
        packages = "psycopg2-binary requests beautifulsoup4 lxml docling"
    else:
        packages = "psycopg2-binary requests beautifulsoup4 lxml"
    
    # Build Docker command
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{os.getcwd()}/{script_name}:/app/{script_name}:ro",
        "--env-file", ".env",
        "--network", "rag_rag-network",
        "python:3.12-slim",
        "sh", "-c",
        f"pip install --quiet {packages} && python /app/{script_name}"
    ]
    
    try:
        # Run the ingestion
        start_time = time.time()
        result = subprocess.run(docker_cmd, check=True)
        duration = time.time() - start_time
        
        print(f"\n✅ {method_name} completed successfully!")
        print(f"⏱️ Duration: {duration:.1f} seconds")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {method_name} failed with exit code {e.returncode}")
        return False
    except KeyboardInterrupt:
        print(f"\n⏹️ {method_name} interrupted by user")
        return False

def run_all_methods():
    """Run all ingestion methods in sequence"""
    methods = [
        ('ingest_docling_simple.py', 'Docling Enhanced Ingestion'),
        ('ingest_standalone_fixed.py', 'Standalone Fixed Ingestion'),
        ('ingest_standalone.py', 'Standalone Basic Ingestion')
    ]
    
    print("\n🔄 Running All Ingestion Methods")
    print("=" * 50)
    
    results = []
    total_start = time.time()
    
    for script, name in methods:
        if os.path.exists(script):
            success = run_docker_ingestion(script, name)
            results.append((name, success))
            
            if success:
                print(f"✅ {name}: SUCCESS")
            else:
                print(f"❌ {name}: FAILED")
                
            # Brief pause between methods
            time.sleep(2)
        else:
            print(f"⚠️ {script} not found, skipping...")
            results.append((name, False))
    
    total_duration = time.time() - total_start
    
    print(f"\n📊 All Methods Complete!")
    print(f"⏱️ Total duration: {total_duration:.1f} seconds")
    print("\nResults:")
    for name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"   {name}: {status}")

def main():
    """Main function"""
    print_banner()
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please configure your .env file.")
        return 1
    
    # Check Docker network
    if not check_docker_network():
        print("\n❌ Docker network check failed. Please start your RAG system.")
        return 1
    
    # Show options
    options = show_ingestion_options()
    
    # Get user choice
    while True:
        try:
            choice = input("🎯 Choose ingestion method (1-4) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("👋 Goodbye!")
                return 0
            
            if choice in ['1', '2', '3']:
                option = options[int(choice) - 1]
                script_name = option['file']
                method_name = option['name']
                
                if not os.path.exists(script_name):
                    print(f"❌ Script {script_name} not found!")
                    continue
                
                success = run_docker_ingestion(script_name, method_name)
                
                if success:
                    print(f"\n🎉 {method_name} completed successfully!")
                    print("💡 Next steps:")
                    print("   1. Check your Streamlit app at http://localhost:8501")
                    print("   2. Try asking questions about your MFS content!")
                else:
                    print(f"\n❌ {method_name} failed. Check the output above for details.")
                
                break
                
            elif choice == '4':
                run_all_methods()
                print(f"\n🎉 All ingestion methods completed!")
                print("💡 Your RAG system now has comprehensive coverage!")
                print("   Visit: http://localhost:8501")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, 4, or 'q'.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return 0
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())