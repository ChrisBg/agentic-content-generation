import os
import sys

# Add the parent directory to sys.path to allow importing src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents import create_content_generation_pipeline

# ADK expects a 'root_agent' variable
root_agent = create_content_generation_pipeline()
