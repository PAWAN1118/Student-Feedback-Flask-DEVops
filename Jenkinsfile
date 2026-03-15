// ─── Student Feedback System — Jenkins CI/CD Pipeline ───────────────
// Pipeline flow: Checkout → Lint → Test → Build Image → Push → Deploy
// All stages run on the Jenkins agent (same machine for local setup).

pipeline {

    agent any

    // ── Environment variables ──────────────────────────────────────
    environment {
        APP_NAME      = 'student-feedback-system'
        IMAGE_NAME    = "student-feedback-system"
        IMAGE_TAG     = "${BUILD_NUMBER}"        // e.g. "42"
        CONTAINER_NAME = 'feedback-app'
        APP_PORT      = '5000'
        HOST_PORT     = '8080'
        ANSIBLE_DIR   = './ansible'
    }

    // ── Pipeline options ───────────────────────────────────────────
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
                sh 'echo "Branch: $(git rev-parse --abbrev-ref HEAD)"'
                sh 'echo "Commit: $(git rev-parse --short HEAD)"'
            }
        }

        // ── Stage 2: Lint & Static Analysis ───────────────────────
        stage('Lint') {
            steps {
                echo "=== Running Python linting ==="
                sh '''
                    pip install --quiet flake8 2>/dev/null || true
                    # Check for syntax errors (E9xx) and undefined names (F821)
                    flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
                    echo "Lint passed!"
                '''
            }
        }

        // ── Stage 3: Unit Tests ────────────────────────────────────
        stage('Test') {
            steps {
                echo "=== Running unit tests ==="
                sh '''
                    pip install --quiet flask pytest 2>/dev/null || true
                    # Run tests if test files exist
                    if [ -d tests ]; then
                        DB_PATH=/tmp/test_feedback.db pytest tests/ -v
                    else
                        echo "No tests directory found — skipping (add tests/ for production!)"
                    fi
                '''
            }
        }

        // ── Stage 4: Build Docker Image ────────────────────────────
        stage('Build Docker Image') {
            steps {
                echo "=== Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG} ==="
                sh '''
                    docker build \
                        --tag ${IMAGE_NAME}:${IMAGE_TAG} \
                        --tag ${IMAGE_NAME}:latest \
                        --label "build=${BUILD_NUMBER}" \
                        --label "commit=$(git rev-parse --short HEAD)" \
                        .
                    echo "Docker image built successfully!"
                    docker images ${IMAGE_NAME}
                '''
            }
        }

        // ── Stage 5: Validate Image ────────────────────────────────
        stage('Validate Image') {
            steps {
                echo "=== Validating Docker image ==="
                sh '''
                    # Run a quick smoke test of the image
                    docker run --rm \
                        --name feedback-smoke-test \
                        -e DB_PATH=/tmp/test.db \
                        -d -p 5099:5000 \
                        ${IMAGE_NAME}:${IMAGE_TAG}

                    # Wait for app to start
                    sleep 8

                    # Check health endpoint
                    HEALTH=$(curl -sf http://localhost:5099/health || echo "FAILED")
                    docker stop feedback-smoke-test || true

                    echo "Health check response: $HEALTH"
                    echo "$HEALTH" | grep -q "ok" && echo "Smoke test PASSED!" || (echo "Smoke test FAILED!" && exit 1)
                '''
            }
        }

        // ── Stage 6: Deploy with Ansible ──────────────────────────
        stage('Deploy') {
            steps {
                echo "=== Deploying with Ansible ==="
                sh '''
                    ansible-playbook \
                        -i ${ANSIBLE_DIR}/inventory \
                        ${ANSIBLE_DIR}/deploy.yml \
                        --extra-vars "image_name=${IMAGE_NAME} image_tag=${IMAGE_TAG} host_port=${HOST_PORT} container_name=${CONTAINER_NAME}" \
                        -v
                '''
            }
        }

        // ── Stage 7: Verify Deployment ────────────────────────────
        stage('Verify Deployment') {
            steps {
                echo "=== Verifying live deployment ==="
                sh '''
                    sleep 5
                    RESPONSE=$(curl -sf http://localhost:${HOST_PORT}/health || echo "FAILED")
                    echo "Live app response: $RESPONSE"
                    echo "$RESPONSE" | grep -q "ok" && echo "Deployment VERIFIED!" || (echo "Deployment FAILED!" && exit 1)
                '''
            }
        }
    }

    // ── Post-build actions ─────────────────────────────────────────
    post {
        success {
            echo """
╔══════════════════════════════════════════╗
║  ✓  PIPELINE SUCCESS                     ║
║     App running at http://localhost:8080  ║
╚══════════════════════════════════════════╝
            """
        }
        failure {
            echo "✗ PIPELINE FAILED — check logs above for details"
            // Clean up any dangling smoke-test containers
            sh 'docker stop feedback-smoke-test 2>/dev/null || true'
        }
        always {
            echo "Build #${BUILD_NUMBER} completed. Cleaning old images..."
            sh '''
                # Remove images older than last 3 builds
                docker images ${IMAGE_NAME} --format "{{.Tag}}" | \
                    sort -rn | tail -n +4 | \
                    xargs -I{} docker rmi ${IMAGE_NAME}:{} 2>/dev/null || true
            '''
        }
    }
}
