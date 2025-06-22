# RE Matching Web

An intelligent web application for pattern matching and data transformation using natural language processing. Upload CSV or Excel files, describe what you want to find in plain English, and let AI automatically detect the right columns and apply smart replacements.

## Table of Contents

- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [DemoVideo](#DemoVideo)



## Tech Stack

### Backend
- **Framework**: Django 5.2.3 with Django REST Framework
- **AI/LLM**: Google Gemini 1.5 Flash
- **Data Processing**: Pandas, regex
- **Database**: SQLite (development)

### Frontend
- **Framework**: React.js with Create React App
- **Styling**: Custom CSS with modern design
- **API Communication**: Fetch API

## Prerequisites

### Backend Requirements
- Python 3.8 or higher

### Frontend Requirements
- Node.js 16.0 or higher
- npm or yarn

### API Requirements
- Google Gemini API key (get one at [Google AI Studio](https://aistudio.google.com/app/apikey))

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/BaitingChen/re_matching_web.git
cd re_matching_web
```
### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source .venv/bin/activate

# Run backend server
python manage.py runserver
```
The Django backend will be available at http://localhost:8000

### 3. Frontend Setup
```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install Node.js dependencies
npm install

npm start
```
The React frontend will open automatically at http://localhost:3000

## Usage
#### Step 1: Upload Your Data
- Drag and drop or click to upload a CSV, XLSX, or XLS file (max 10MB)
- Supported formats: CSV, Excel files with tabular data

#### Step 2: Preview Your Data
- Review the uploaded data structure
- See which columns contain text data (highlighted in blue)
- Only text columns can be processed for pattern matching

#### Step 3: Configure Pattern Matching
- **Enter your Gemini API Key**: Required for AI-powered pattern detection
- **Describe what to find**: Use natural language like:
  - "find email addresses"
  - "find names and emails"
  - "find phone numbers"
  - "find IP addresses"
- **Set replacement value**: What to replace matches with (e.g., "REDACTED", "[HIDDEN]")

#### Step 4: View Results
- See original vs processed data side-by-side
- Review replacement statistics by column
- Download the processed data as CSV

## DemoVideo
[Demo Video Link](https://github.com/BaitingChen/re_matching_web/blob/main/demovideo/demo-video.mp4)
