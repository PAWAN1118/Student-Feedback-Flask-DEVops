# FeedLoop — Student Feedback System

A full-stack web application with a local DevOps pipeline:
**Git → Jenkins → Docker → Ansible → Running App**

---

## Project Structure

```
student-feedback-system/
├── app/
│   ├── app.py           # Flask application (routes)
│   ├── database.py      # SQLite database layer
│   └── requirements.txt
├── templates/
│   ├── index.html       # Dashboard (view all feedback)
│   └── feedback.html    # Submit feedback form
├── static/
│   └── style.css        # Dark-theme stylesheet
├── Dockerfile           # Multi-stage Docker build
├── Jenkinsfile          # CI/CD pipeline definition
├── ansible/
│   ├── inventory        # Ansible hosts (localhost)
│   └── deploy.yml       # Deployment playbook
└── README.md
```

---

## Quick Start (Manual — No Jenkins)

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd student-feedback-system

# 2. Build the Docker image
docker build -t student-feedback-system:latest .

# 3. Create a volume for persistent data
docker volume create feedback_data

# 4. Run the container
docker run -d \
  --name feedback-app \
  -p 8080:5000 \
  -v feedback_data:/data \
  student-feedback-system:latest

# 5. Open in browser
open http://localhost:8080
```

---

## Full DevOps Pipeline Setup

### Prerequisites

Install on your machine:

| Tool    | Version  | Purpose                     |
|---------|----------|-----------------------------|
| Git     | Latest   | Version control             |
| Docker  | 24+      | Containerisation            |
| Jenkins | LTS      | CI/CD automation            |
| Ansible | 2.15+    | Deployment automation       |
| Python  | 3.10+    | Runtime                     |

### Step 1 — Start Jenkins

```bash
# Using Docker (easiest)
docker run -d \
  --name jenkins \
  -p 8081:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts

# Get the initial admin password
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

### Step 2 — Configure Jenkins

1. Open http://localhost:8081
2. Install suggested plugins
3. Create admin user
4. Install additional plugins: **Docker Pipeline**, **Ansible**

### Step 3 — Create Pipeline Job

1. **New Item** → "student-feedback" → **Pipeline**
2. Under *Pipeline*: select **Pipeline script from SCM**
3. SCM: **Git** → enter your repository URL
4. Script Path: `Jenkinsfile`
5. Save

### Step 4 — Configure GitHub Webhook (optional)

In your GitHub repo:
- Settings → Webhooks → Add webhook
- Payload URL: `http://<your-ip>:8081/github-webhook/`
- Content type: `application/json`
- Events: **Just the push event**

### Step 5 — Run the Pipeline

Click **Build Now** in Jenkins, or push code to GitHub.

Watch the pipeline:
```
Checkout → Lint → Test → Build Image → Validate → Deploy → Verify
```

App will be live at: **http://localhost:8080**

---

## Ansible — Manual Deploy

```bash
# Deploy manually (after building the image)
ansible-playbook \
  -i ansible/inventory \
  ansible/deploy.yml \
  --extra-vars "image_name=student-feedback-system image_tag=latest host_port=8080"
```

---

## Useful Docker Commands

```bash
# View running containers
docker ps

# View app logs
docker logs feedback-app -f

# Stop the app
docker stop feedback-app

# Check health
curl http://localhost:8080/health

# Enter container shell
docker exec -it feedback-app /bin/bash
```

---

## Learning Objectives

After completing this project, students will understand:

- **Flask**: Building web apps with Python, Jinja2 templates, form handling
- **SQLite**: Persistent storage without an external DB server
- **Docker**: Multi-stage builds, volumes, health checks, non-root users
- **Jenkins**: Declarative pipelines, stages, post-build actions
- **Ansible**: Idempotent playbooks, inventory, variables, URI module
- **DevOps workflow**: How code changes flow from developer to production

---

## Tech Stack

- **Backend**: Python 3.12 + Flask 3.0 + Gunicorn
- **Database**: SQLite (via Docker named volume)
- **Frontend**: HTML5 + CSS3 (dark theme, responsive)
- **Container**: Docker (multi-stage build)
- **CI/CD**: Jenkins (declarative pipeline)
- **Deployment**: Ansible playbook
