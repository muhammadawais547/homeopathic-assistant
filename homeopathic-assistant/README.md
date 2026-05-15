# Homeopathic Assistant

A desktop application for homeopathic practitioners to manage patient records and recommend remedies based on symptom matching using Kent's Repertory.

## Features
- Add and view patients
- Search for patients by ID
- Find remedies by symptoms using full‑text search
- Import Kent's Repertory into MySQL

## Requirements
- Python 3.8+
- MySQL server
- PyQt6
- mysql-connector-python

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Create a MySQL database named `homoeo` and run the schema (see schema.sql).
3. Update `config.py` with your database credentials.
4. Place `kent.txt` in the project root.
5. Run the import script: `python scripts/import_kent.py` (this may take several minutes).
6. Start the application: `python main.py`

## Usage
- **Add Patient**: Fill in the form and save. A unique Patient ID is generated.
- **View Patients**: Browse all patients, search by ID, view details.
- **Find Remedies**: Enter symptoms (one per line), optionally select thermal type, and get ranked remedies with color‑coded match levels.

## Database Schema
(Include brief schema description)