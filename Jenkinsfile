pipeline {
    // Use an agent that has Docker, Python, and SonarScanner CLI installed.
    agent any

    // Define tools from Jenkins Global Tool Configuration
    tools {
        // This name must match the one in Manage Jenkins -> Global Tool Configuration
        sonarScanner 'SonarScanner'
    }

    environment {
        // SonarQube server name from Jenkins system config
        SONAR_SERVER = 'my-sonarqube-server'
        // Docker registry URL (e.g., your Docker Hub username or private registry)
        DOCKER_REGISTRY = 'your-docker-registry-placeholder'
        // Define your application name for the Docker image
        APP_NAME = 'video-summarizer'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code...'
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Installing Python dependencies...'
                // Install dependencies without running tests (no tests detected in project)
                sh 'python -m venv venv'
                sh '. venv/bin/activate && pip install -r requirements.txt'
            }
        }

        stage('SonarQube Analysis') {
            steps {
                echo 'Running SonarQube analysis...'
                // withSonarQubeEnv sets up environment variables for the scanner
                withSonarQubeEnv(SONAR_SERVER) {
                    // 'sonarScanner' is the tool name from Global Tool Configuration
                    // The scanner will automatically pick up the server URL and token
                    sh 'sonar-scanner -Dsonar.python.coverage.reportPaths=coverage.xml || echo "Coverage report not found, continuing."'
                }
            }
        }

        stage('Quality Gate Check') {
            steps {
                echo 'Checking SonarQube Quality Gate status...'
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build and Push Docker Image') {
            when {
                // Only run this stage for the 'main' or 'master' branch
                branch 'main'
            }
            steps {
                script {
                    echo 'Building and pushing Docker image...'
                    // Use the build number as the image version for traceability
                    def imageVersion = env.BUILD_NUMBER
                    def imageName = "${env.DOCKER_REGISTRY}/${env.APP_NAME}:${imageVersion}"
                    def latestImageName = "${env.DOCKER_REGISTRY}/${env.APP_NAME}:latest"

                    // Use the Docker Pipeline plugin to build and push
                    docker.withRegistry('https://index.docker.io/v1/', 'DOCKER_CREDENTIALS') {
                        def dockerImage = docker.build(imageName, '.')
                        dockerImage.push()
                        dockerImage.push(latestImageName)
                    }
                }
            }
        }
    }
    post {
        always {
            echo 'Pipeline finished.'
            cleanWs()
        }
    }
}
