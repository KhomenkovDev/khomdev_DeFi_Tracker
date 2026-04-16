# KhomDev Finance Engine

<div align="center">
  <img src="icon.png" width="150" alt="KhomDev Finance Engine" />
</div>

![Screenshot 1](screenshots/Screenshot%202026-04-16%20at%2020.51.02.png)
![Screenshot 2](screenshots/Screenshot%202026-04-16%20at%2020.51.09.png)
A professional, robust Django-based application designed for comprehensive financial analysis, portfolio management, and market insights. Finance Multitool combines robust backend data processing with an elegant, user-friendly frontend to deliver a powerful experience for traders and developers alike.

## 🚀 Live Demo

[Launch KhomDev Finance Engine Live](https://khomdev-finance-engine-87824241220.us-central1.run.app)
*(Hosted continuously on Google Cloud Run)*

## Features

- **Interactive Financial Charts**: Professional-grade, interactive financial charts powered by TradingView Lightweight Charts, perfect for visualizing historical and real-time market data.
- **Persistent User Watchlists**: Create and manage personalized watchlists. The application persistently stores your watchlisted assets, making it easy to track your favorite financial instruments.
- **High-Performance Memory Caching**: Optimized for speed. The application employs high-performance memory caching to minimize redundant data requests and ensure lightning-fast load times.
- **Advanced Technical Analysis**: Leverage the power of `pandas` and `numpy` for comprehensive and advanced technical analysis on financial data, enabling complex computations and custom indicators.
- **AI-Driven Market Insights**: Seamlessly integrated with Google GenAI / Gemini to provide deep, AI-driven market analysis and insights on your financial data.
- **Robust Data Handling**: Efficient data fetching via `yfinance`, allowing the application to pull reliable market data quickly.
- **Clean UI & Responsive Design**: A beautifully crafted user interface relying on modern web standards, prioritizing user experience and aesthetic appeal.

## Technology Stack

- **Backend**: Python 3, Django 4.2
- **Data & Analysis**: pandas, numpy, yfinance
- **AI Integration**: Google GenAI
- **Frontend**: HTML5, CSS3, JavaScript (TradingView Lightweight Charts)
- **Database**: SQLite (built-in storage for watchlists and user data)

## Installation

### Prerequisites

Ensure you have Python 3.9+ installed on your system.

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/KhomenkovDev/khomdev_finance_engine.git
   cd finance_multitool
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory. You will need to add your specific API keys, such as your Google GenAI API key.
   ```env
   GEMINI_API_KEY=your_genai_api_key_here
   # Add any other required environment settings (e.g., DJANGO_SECRET_KEY, DEBUG)
   ```

5. **Apply Database Migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Run the Development Server:**
   ```bash
   python manage.py runserver
   ```

7. **Access the Application:**
   Open your browser and navigate to `http://127.0.0.1:8000/`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an issue if you encounter any bugs or have feature suggestions.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
