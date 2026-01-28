# Career Compass AI 🧭

Career Compass AI is a powerful, AI-driven career counseling platform that provides personalized professional recommendations. By leveraging Google's Gemini Flash AI, the application analyzes your qualifications, skills, and interests to generate tailored career roadmaps, education paths, and industry insights.

## ✨ Features

- **AI-Powered Analysis**: Uses Gemini 1.5 Flash to provide high-quality, personalized career advice.
- **Dual Guidance Modes**: Supports both "Higher Studies" for academic paths and "Job Placements" for professional transitions.
- **Structured Recommendations**: Each path includes an overview, detailed steps, pros/cons, and specific resources.
- **PDF Report Generation**: Export your personalized career roadmap into a beautifully formatted PDF document.
- **Secure Configuration**: Uses environment variables for API key management, making it safe for deployment and version control.
- **Premium UI/UX**: Clean, responsive, and intuitive interface designed for a modern user experience.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- A Google Gemini API Key (get one at [Google AI Studio](https://aistudio.google.com/))

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/career-compass-ai.git
   cd career-compass-ai
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in the root directory and add your API key:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   FLASK_DEBUG=True
   SECRET_KEY=your_generated_secret_key
   ```

### Running the Application

Start the Flask development server:
```bash
python app.py
```
The application will be available at `http://localhost:5000`.

## 📁 Project Structure

```text
career-compass-ai/
├── templates/          # HTML templates for the Flask UI
├── app.py              # Main Flask application logic
├── .env                # Environment variables (private)
├── .gitignore          # Files to exclude from Git
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

## 🛡️ Security

This project uses `python-dotenv` to manage sensitive information. **Never commit your `.env` file to version control.** The `.gitignore` file included in this repository is pre-configured to exclude `.env` and other sensitive files.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---
*Built with ❤️ by Career Compass AI Team*
