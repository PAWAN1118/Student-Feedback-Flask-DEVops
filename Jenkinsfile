// ─── Student Feedback System — Jenkins CI/CD Pipeline (Windows) ─────
// Pipeline flow: Checkout → Lint → Test → Build Image → Validate → Deploy → Verify

pipeline {

    agent any

    environment {
        APP_NAME       = 'student-feedback-system'
        IMAGE_NAME     = 'student-feedback-system'
        IMAGE_TAG      = "${BUILD_NUMBER}"
        CONTAINER_NAME = 'feedback-app'
        APP_PORT       = '5000'
        HOST_PORT      = '8080'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 20, unit: 'MINUTES')
        timestamps()
    }

    stages {

        // ── Stage 1: Checkout ──────────────────────────────────────
        stage('Checkout') {
            steps {
                echo "=== Checking out source code ==="
                checkout scm
                bat 'git rev-parse --abbrev-ref HEAD'
                bat 'git rev-parse --short HEAD'
            }
        }

        // ── Stage 2: Lint ──────────────────────────────────────────
        stage('Lint') {
            steps {
                echo "=== Running Python linting ==="
                bat '''
                    where pip >nul 2>&1
                    if %errorlevel% neq 0 (
                        echo WARNING: pip not found - skipping lint
                        exit /b 0
                    )
                    pip install --quiet flake8
                    flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
                    echo Lint passed!
                '''
            }
        }

        // ── Stage 3: Test ──────────────────────────────────────────
        stage('Test') {
            steps {
                echo "=== Running unit tests ==="
                bat '''
                    where pip >nul 2>&1
                    if %errorlevel% neq 0 (
                        echo WARNING: pip not found - skipping tests
                        exit /b 0
                    )
                    if exist tests (
                        pip install --quiet flask pytest
                        set DB_PATH=%TEMP%\\test_feedback.db
                        pytest tests/ -v
                    ) else (
                        echo No tests directory found - skipping
                    )
                '''
            }
        }

        // ── Stage 4: Build Docker Image ────────────────────────────
        stage('Build Docker Image') {
            steps {
                echo "=== Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG} ==="
                bat '''
                    docker build ^
                        --tag %IMAGE_NAME%:%IMAGE_TAG% ^
                        --tag %IMAGE_NAME%:latest ^
                        --label "build=%BUILD_NUMBER%" ^
                        .
                    echo Docker image built successfully!
                    docker images %IMAGE_NAME%
                '''
            }
        }

        // ── Stage 5: Validate Image ────────────────────────────────
        stage('Validate Image') {
            steps {
                echo "=== Running smoke test ==="
                bat '''
                    docker run -d ^
                        --name feedback-smoke-test ^
                        -e DB_PATH=C:/tmp/test.db ^
                        -p 5099:5000 ^
                        %IMAGE_NAME%:%IMAGE_TAG%

                    timeout /t 12 /nobreak

                    curl -f http://localhost:5099/health
                    if %errorlevel% neq 0 (
                        echo Smoke test FAILED!
                        docker stop feedback-smoke-test
                        docker rm feedback-smoke-test
                        exit /b 1
                    )

                    docker stop feedback-smoke-test
                    docker rm feedback-smoke-test
                    echo Smoke test PASSED!
                '''
            }
        }

        // ── Stage 6: Deploy ────────────────────────────────────────
        stage('Deploy') {
            steps {
                echo "=== Deploying application container ==="
                bat '''
                    docker stop %CONTAINER_NAME% 2>nul
                    docker rm   %CONTAINER_NAME% 2>nul

                    docker volume create feedback_data

                    docker run -d ^
                        --name %CONTAINER_NAME% ^
                        --restart unless-stopped ^
                        -p %HOST_PORT%:%APP_PORT% ^
                        -v feedback_data:/data ^
                        -e DB_PATH=/data/feedback.db ^
                        -e FLASK_ENV=production ^
                        %IMAGE_NAME%:%IMAGE_TAG%

                    echo Container started successfully!
                    docker ps --filter name=%CONTAINER_NAME%
                '''
            }
        }

        // ── Stage 7: Verify Deployment ────────────────────────────
        stage('Verify Deployment') {
            steps {
                echo "=== Verifying live deployment ==="
                bat '''
                    timeout /t 8 /nobreak
                    curl -f http://localhost:%HOST_PORT%/health
                    if %errorlevel% neq 0 (
                        echo Deployment verification FAILED!
                        exit /b 1
                    )
                    echo Deployment VERIFIED! App is live at http://localhost:%HOST_PORT%
                '''
            }
        }
    }

    post {
        success {
            echo '=== PIPELINE SUCCESS - App running at http://localhost:8080 ==='
        }
        failure {
            echo 'PIPELINE FAILED - check logs above for details'
            bat 'docker stop feedback-smoke-test 2>nul & docker rm feedback-smoke-test 2>nul & exit /b 0'
        }
        always {
            echo "Build #${BUILD_NUMBER} completed."
        }
    }
}
