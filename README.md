# Embu DevRec Hub - Records System

A web-based records management system designed to help organize and track development records for Embu County.

The system provides a simples and secure way to store, search, update and manage records, replacing manual paperwork with a fast digital solution.

## Features
- Add, view, edit and delete records
- Search records easily
- User-friendly web interface
- Built with Python flask

## Basic operation used to manage DataBase recordS
CRUD
C - Create
R - Read
U - Update
D - Delete

## Technologies Used
- Python (Flask) - programming language for developing the system and flask - help python run the web application
- HTML, CSS - creating webpages & styling
- SQLite Database - stores the system's records
- SQL Alchemy - helps python communicate with the database
- Javascript - add interractivity to the pages
- SHA-256 - Help generate a unique- looking for the records
- HMAC (Hash-based Message Authenticatio Code) - ensure information not tempared with by verfying the authenticity and integrity of records

## How to Run
1. Install requirements: pip install -r requirements.txt
2. Run: python app.py
3. Open in browser: http://127.0.0.1:5000

## Project Files
- app.py - Main application
- templates/ - HTML pages
- API_Communication_System_Presentation.pptx - Project presentation
- DEPLOYMENT.md - Deployment guide
- Requirement.txt - List of Python packages needed to run the project
- wsgi.py - Entry point for deploying the app on a server
- test_app.py - Tests to check if the app works correctly
- result.txt - Test / output results
- instance/ - Folder holding the database and instance files
- ____pycache_____/ - Auto-generated python cache files (created when the app runs)
