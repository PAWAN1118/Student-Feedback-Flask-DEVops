// ─── Student Feedback System — Jenkins CI/CD Pipeline (Windows + Ansible) ───

pipeline {

    agent any

    environment {
        IMAGE_NAME     = 'student-feedback-system'
        IMAGE_TAG      = "${BUILD_NUMBER}"
        CONTAINER_NAME = 'feedback-app'
        APP_PORT       = '5000'
        HOST_PORT      = '8090'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 20, unit: 'MINUTES')
        timestamps()
    }

    stages {

        stage('Checkout') {
            steps {
                echo "=== Checking out source code ==="
                checkout scm
                bat 'git rev-parse --short HEAD'
            }
        }

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
                        set DB_PATH=/tmp/test_feedback.db
                        pytest tests/ -v
                    ) else (
                        echo No tests directory found - skipping
                    )
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "=== Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG} ==="
                bat '''
                    docker build ^
                        --tag %IMAGE_NAME%:%IMAGE_TAG% ^
                        --tag %IMAGE_NAME%:latest ^
                        --label "build=%BUILD_NUMBER%" ^
                        .
                    if %errorlevel% neq 0 (
                        echo Docker build FAILED!
                        exit /b 1
                    )
                    echo Docker image built successfully!
                    docker images %IMAGE_NAME%
                '''
            }
        }

        stage('Validate Image') {
            steps {
                echo "=== Running smoke test ==="
                bat '''
                    docker run -d ^
                        --name feedback-smoke-test ^
                        -e DB_PATH=/tmp/test.db ^
                        -p 5099:5000 ^
                        %IMAGE_NAME%:%IMAGE_TAG%

                    if %errorlevel% neq 0 (
                        echo Failed to start smoke test container!
                        exit /b 1
                    )

                    echo Waiting for container to start...
                    ping -n 14 127.0.0.1 >nul

                    curl -f http://localhost:5099/health
                    if %errorlevel% neq 0 (
                        echo Smoke test FAILED!
                        docker logs feedback-smoke-test
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

        // ── Stage 6: Deploy with Ansible ──────────────────────────
        // Uses a custom Ansible+Docker image built on the fly.
        // This ensures both ansible and docker CLI are available.
        stage('Deploy with Ansible') {
            steps {
                echo "=== Building Ansible+Docker image ==="
                bat '''
                    :: Write a temporary Dockerfile for Ansible+Docker CLI
                    echo FROM python:3.11-slim > AnsibleDockerfile
                    echo RUN apt-get update -qq ^&^& apt-get install -y -qq docker.io ^&^& rm -rf /var/lib/apt/lists/* >> AnsibleDockerfile
                    echo RUN pip install --quiet ansible >> AnsibleDockerfile

                    :: Build the Ansible+Docker image
                    docker build -f AnsibleDockerfile -t ansible-with-docker:local .
                    if %errorlevel% neq 0 (
                        echo Failed to build Ansible image!
                        exit /b 1
                    )

                    echo Running Ansible playbook...
                    docker run --rm ^
                        -v %CD%:/workspace ^
                        -w /workspace ^
                        --add-host=host.docker.internal:host-gateway ^
                        -v //var/run/docker.sock:/var/run/docker.sock ^
                        ansible-with-docker:local ^
                        ansible-playbook ^
                            -i ansible/inventory ^
                            ansible/deploy.yml ^
                            --extra-vars "image_name=%IMAGE_NAME% image_tag=%IMAGE_TAG% host_port=%HOST_PORT% container_name=%CONTAINER_NAME%" ^
                            -v

                    if %errorlevel% neq 0 (
                        echo Ansible deployment FAILED!
                        exit /b 1
                    )
                    echo Ansible deployment complete!
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                echo "=== Verifying live deployment ==="
                bat '''
                    ping -n 10 127.0.0.1 >nul
                    curl -f http://localhost:%HOST_PORT%/health
                    if %errorlevel% neq 0 (
                        echo Verification FAILED!
                        docker logs %CONTAINER_NAME%
                        exit /b 1
                    )
                    echo Deployment VERIFIED! App is live at http://localhost:%HOST_PORT%
                '''
            }
        }
    }

    post {
        success {
            echo '=== PIPELINE SUCCESS - App running at http://localhost:8090 ==='
        }
        failure {
            echo 'PIPELINE FAILED - check logs above'
            bat 'docker stop feedback-smoke-test 2>nul & docker rm feedback-smoke-test 2>nul & exit /b 0'
        }
        always {
            echo "Build #${BUILD_NUMBER} completed."
        }
    }
}
