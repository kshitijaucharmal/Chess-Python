import sys
import os

# Add the project root to sys.path to allow running from anywhere
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    from src.main import main
    main()
