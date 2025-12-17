# Video Summarizer Web App

A Flask-based web application that summarizes videos by detecting and highlighting significant motion, with user authentication and password reset functionality.

## Features

- **Video Summarization**: Upload videos and get summarized versions focusing on motion detection
- **User Authentication**: Secure login and registration system
- **Password Reset**: Email-based password recovery
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Responsive UI**: Clean web interface for video uploads and management

## Prerequisites

- Python 3.8+
- Docker and Docker Compose (for containerized deployment)
- OpenCV-compatible environment (includes numpy, opencv-python)

## Repository Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/AryanKale-git/Video-Summarization-Docker.git
   cd video-summ-docker
   ```

2. **Create and switch to a feature branch** (for development):
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Pull latest changes** (before starting work):
   ```bash
   git pull origin main
   ```

4. **Make changes and commit**:
   ```bash
   git add .
   git commit -m "Add your commit message here"
   ```

5. **Push your changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a pull request** (after pushing):
   ```bash
   gh pr create --title "Your PR title" --body "Description of changes"
   ```
   *Note: Requires GitHub CLI (`gh`) to be installed. Install with: `winget install --id GitHub.cli` (Windows) or follow [GitHub CLI installation guide](https://cli.github.com/).*

### Additional Git Commands

- **Check repository status**:
  ```bash
  git status
  ```

- **View commit history**:
  ```bash
  git log --oneline
  ```

- **View differences before committing**:
  ```bash
  git diff
  ```

- **Stash uncommitted changes**:
  ```bash
  git stash
  ```

- **Apply stashed changes**:
  ```bash
  git stash pop
  ```

- **Fetch latest changes without merging**:
  ```bash
  git fetch origin
  ```

- **Delete a local branch** (after merging):
  ```bash
  git branch -d feature/your-feature-name
  ```

## Installation

### Local Development

1. Clone the repository (see Repository Setup above).

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with:
   ```
   SECRET_KEY=your-secret-key-here
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_ADDRESS=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   SERVER_NAME=localhost:5000
   ```

5. Initialize the database:
   ```bash
   flask init-db
   ```

6. Run the application:
   ```bash
   python app.py
   ```

   The app will be available at `http://localhost:5000`

### Docker Deployment

1. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

2. The app will be available at `http://localhost:5000`

## Usage

1. **Register**: Create a new account at `/register`
2. **Login**: Access your account at `/login`
3. **Upload Video**: On the main page, upload a video file (.mp4, .avi, .mov)
4. **Download Summary**: The app will process the video and provide a download link for the summarized version
5. **Password Reset**: Use `/forgot_password` if you forget your password

## Environment Variables

- `SECRET_KEY`: Flask secret key for sessions (required)
- `SMTP_SERVER`: SMTP server for email (default: smtp.gmail.com)
- `SMTP_PORT`: SMTP port (default: 587)
- `EMAIL_ADDRESS`: Email address for sending password resets (required for password reset)
- `EMAIL_PASSWORD`: Email password/app password (required for password reset)
- `SERVER_NAME`: Server name for URL generation (e.g., localhost:5000)
- `PORT`: Port to run the app on (default: 5000)

## Project Structure

```
.
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container configuration
├── docker-compose.yml    # Docker Compose setup
├── templates/            # HTML templates
│   ├── login.html
│   ├── register.html
│   ├── forgot_password.html
│   ├── reset_password.html
│   └── video_summarizer.html
├── uploads/              # Temporary upload directory
└── README.md            # This file
```

## API Endpoints

- `GET /`: Main page (requires login)
- `GET/POST /login`: User login
- `GET/POST /register`: User registration
- `GET/POST /forgot_password`: Password reset request
- `GET/POST /reset_password/<token>`: Password reset with token
- `POST /upload`: Video upload and processing
- `GET /logout`: User logout

## Video Processing

The summarization algorithm:
- Uses background subtraction to detect motion
- Applies morphological operations to clean noise
- Filters contours based on area (>1500 pixels)
- Only includes frames with significant movement in the output
- Reduces output FPS by half for efficiency

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security Notes

- Passwords are hashed using Werkzeug's secure hashing
- File uploads are validated for type and secured with Werkzeug
- Temporary files are cleaned up after processing
- Email credentials should be stored securely (not in version control)
