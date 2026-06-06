# AI-Powered Personalized Cover Letter Generator & Interview Prep

An intelligent, modular toolkit for job seekers built on local LLMs (Ollama) and PaddleOCR. 
This Streamlit-based application assists users in generating highly professional cover letters, scoring resumes against Job Descriptions (ATS match), and conducting simulated AI mock interviews—all while keeping data locally processed for complete privacy.

## ✨ Features

- **Cover Letter Generator:** Automatically drafts a professional, heavily tailored cover letter based on your resume and a target job description. Includes a built-in text editor to review, copy, and export the final letter directly as a `.txt` file.
- **ATS Match Score:** Acts as an Applicant Tracking System. It scores your resume against a job description, displays visual progress metrics, and gives actionable advice on missing keywords.
- **Simulated Interview Prep:** Conducts a technical and behavioral mock interview step-by-step. The AI asks one question at a time, evaluates your response, and gives constructive feedback before moving on.
- **Robust Local OCR:** Upload your resume or job descriptions in PDF, PNG, or JPG formats. It uses PaddleOCR and PyMuPDF to extract and read document content automatically.
- **Dynamic Model Selection:** Automatically detects available local LLMs from your Ollama instance, allowing you to seamlessly switch between models right from the sidebar.

## 📁 Project Structure

The codebase is organized professionally into modular utilities for better readability:
- `app.py`: The main Streamlit User Interface.
- `utils/llm.py`: Handles Ollama API connections and native UI streaming.
- `utils/ocr.py`: Handles text extraction from PDFs and Images.
- `utils/prompts.py`: Stores all LLM system prompts and instructions.
- `utils/state.py`: Manages the chat history and JSON database.

## 🚀 How to Execute the Project

### 1. Prerequisites
- **Python 3.10+** installed on your system.
- **Ollama**: Download and install Ollama from [ollama.com](https://ollama.com/).

### 2. Download a Local AI Model
Open your terminal and pull a preferred local model via Ollama. If your hardware is memory-constrained (less than 16GB RAM), it is highly recommended to use a lightweight model like `llama3.2:1b`.

```bash
ollama pull llama3.2:1b
```
*(The app will automatically detect any downloaded models and add them to the sidebar dropdown).*

### 3. Setup the Python Environment
Navigate to the project directory, activate your virtual environment, and install dependencies:

```bash
# On Windows (PowerShell/Command Prompt):
.\venv310\Scripts\activate

# Install the necessary dependencies (if you haven't already):
pip install -r requirements.txt
```

### 4. Run the Application
With the virtual environment activated, start the Streamlit application by running:

```bash
streamlit run app.py
```

The app will instantly launch in your default web browser (usually at `http://localhost:8501`).

## 🔒 Privacy

Because this application relies on a local Ollama instance rather than external APIs (like OpenAI), all data processing, resumes, and job descriptions remain entirely offline and private on your local hardware.
