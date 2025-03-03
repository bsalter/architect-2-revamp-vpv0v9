#!/usr/bin/env python3
"""
Interaction Management System Backend
====================================

This module defines the package configuration for the Interaction Management System backend.
It specifies metadata, dependencies, and installation requirements for packaging the
Flask-based API that powers the Interaction Management System.
"""

import os  # version: standard library
import io  # version: standard library
import setuptools  # version: standard library

from . import __version__  # Import version from package __init__.py

# Base directory path for file references
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def read_requirements():
    """
    Read package requirements from the requirements.txt file.
    
    Returns:
        list: List of package requirements
    """
    requirements_path = os.path.join(BASE_DIR, 'requirements.txt')
    try:
        with io.open(requirements_path, encoding='utf-8') as f:
            requirements = f.read().splitlines()
            # Filter out comments and empty lines
            requirements = [line.strip() for line in requirements 
                           if line.strip() and not line.startswith('#')]
            return requirements
    except FileNotFoundError:
        # If requirements.txt is not found, return an empty list
        # or you could raise an error depending on your preference
        return []

setuptools.setup(
    name="interaction_management_backend",
    version=__version__,
    author="Interaction Management System Team",
    author_email="team@interactionmanagement.example.com",
    description="Backend API for the Interaction Management System",
    long_description="""
    A Flask-based RESTful API backend for the Interaction Management System.
    This system provides centralized, searchable interaction management 
    with multi-site support and secure user access control.
    """,
    long_description_content_type="text/markdown",
    url="https://github.com/organization/interaction-management-system",
    packages=setuptools.find_packages(),
    install_requires=read_requirements(),
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: Flask",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    entry_points={
        'console_scripts': [
            'interaction-api=interaction_management_backend.app:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)