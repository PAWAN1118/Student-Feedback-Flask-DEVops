// ─── Student Feedback System — Jenkins CI/CD Pipeline (Windows + Ansible) ───
// Ansible runs inside a Docker container to work on Windows Jenkins.
// Pipeline: Checkout → Lint → Test → Build → Validate → Deploy(Ansible) → Verify

pipeline {

    agent any

    environment {
        IMAGE_NAME     = 'student-feedback-system'
        IMAGE_TAG      = "${BUILD_NUMBER}"
        CONTAINER_NAME = 'feedback-app'
        APP_PORT       = '5000'
        HOST_PORT      = '8090'
        ANSIBLE_IMAGE  = 'cytopia/ansible:latest'
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
                        set DB_PATH=/tmp/test_feedback.db
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
                    if %errorlevel% neq 0 (
                        echo Docker build FAILED!
                        exit /b 1
                    )
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

        // ── Stage 6: Deploy with Ansible (inside Docker) ──────────
        // Ansible doesn't run natively on Windows, so we run it
        // inside a lightweight Docker container that has Ansible
        // pre-installed. We mount the Docker socket so Ansible
        // can control Docker on the host machine.
        stage('Deploy with Ansible') {
            steps {
                echo "=== Deploying with Ansible (running in Docker) ==="
                bat '''
                    :: Pull Ansible Docker image if not present
                    docker pull %ANSIBLE_IMAGE%

                    :: Run Ansible playbook inside a container
                    :: --rm            = remove container after run
                    :: -v /var/run/docker.sock = share Docker socket (Linux/WSL)
                    :: -v workspace    = mount our repo so playbook is accessible
                    :: host.docker.internal = resolves to host machine from container

                    docker run --rm ^
                        -v %CD%:/workspace ^
                        -w /workspace ^
                        --add-host=host.docker.internal:host-gateway ^
                        -v //var/run/docker.sock:/var/run/docker.sock ^
                        %ANSIBLE_IMAGE% ^
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

        // ── Stage 7: Verify Deployment ────────────────────────────
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
