# SIH 2025 - EMR Integration Gateway (Problem ID: 25026)

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-green.svg)

A backend service built for the Smart India Hackathon 2025 to facilitate the integration of standardized medical terminologies into existing EMR systems using the FHIR R4 standard.

---

## 🎯 Problem Statement

> > Develop API code to integrate NAMASTE and/or the International Classification of Diseases (ICD-11) via the Traditional Medicine Module 2 (TM2) into existing EMR systems that comply with Electronic Health Record (EHR) Standards for India. 

## ✨ Our Solution

This project is a Python-based API gateway built with **FastAPI**. It acts as a middleware translator that solves the core problem by:
1.  Receiving standardized data through a REST API endpoint.
2.  Validating and transforming this data into a compliant **FHIR R4 resource**.
3.  Sending the formatted FHIR resource to a target EMR system, ensuring compliance with India's ABDM (Ayushman Bharat Digital Mission) guidelines.

## 🛠️ Tech Stack

* **Backend**: 🐍 Python, 🚀 FastAPI
* **FHIR Library**: 🔥 `fhir.resources` for creating FHIR R4 objects.
* **API Server**: 🦄 Uvicorn
* **HTTP Client**: `requests` for communicating with external systems.

## 📂 Project Structure

```
.
├── backend/
│   ├── main.py       # FastAPI application and core logic.
│   └── [module].py   # (Optional) Additional helper modules.
├── frontend/         # Placeholder for the frontend application.
├── .gitignore        # Specifies files to be ignored by Git.
├── .venv/            # Local Python virtual environment (ignored by Git).
└── requirements.txt  # A list of all Python dependencies.
```

## 🚀 Getting Started

Follow these instructions to get the backend server up and running on your local machine.

### 1. Prerequisites

- Python 3.10+
- Git

### 2. Clone the Repository

Fork the repository first, and then clone your forked version:
```bash
git clone [https://github.com/](https://github.com/)[YOUR_USERNAME]/[YOUR_REPO_NAME].git
cd [YOUR_REPO_NAME]
```

### 3. Set Up the Virtual Environment

Create and activate a virtual environment to keep dependencies isolated.

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows:**
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### 4. Install Dependencies

Install all the required Python libraries from the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

## ⚡ How to Run the Project

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
2.  Start the FastAPI server using Uvicorn:
    ```bash
    uvicorn main:app --reload
    ```
    The `--reload` flag automatically restarts the server when you make changes.

3.  The API is now live and accessible at:
    * **API URL**: `http://1227.0.0.1:8000`
    * **Interactive Docs (Swagger UI)**: `http://1227.0.0.1:8000/docs`

## 📖 API Endpoints

This section documents the primary API endpoints. You can test all endpoints via the interactive Swagger UI.

### Create a New Record

- **URL**: `/record-diagnosis`
- **Method**: `POST`
- **Description**: Converts a simple data input into a FHIR R4 resource.
- **Request Body**:

  ```json
  {
    "patient_id": "[Example_Patient_ID]",
    "code": "[Example_Code]",
    "system": "[Example_Coding_System]",
    "display": "[Example_Display_Text]"
  }
  ```

- **Success Response (200 OK)**: Returns the full FHIR JSON object.

## 🤝 How to Contribute

We follow the standard GitHub Fork & Pull Request workflow.

1.  **Fork** the repository.
2.  Create a new branch for your feature (`git checkout -b feature/MyNewFeature`).
3.  Make your changes and **commit** them (`git commit -m 'Add: Some Amazing Feature'`).
4.  **Push** to your branch (`git push origin feature/MyNewFeature`).
5.  Open a **Pull Request** back to the `main` branch of the original repository.

---
