from flask import Flask, render_template, request, redirect, url_for, flash
from app.database import init_db, add_feedback, get_all_feedback

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = 'student-feedback-secret-key'

# Initialize the database on startup
init_db()

@app.route('/')
def index():
    feedbacks = get_all_feedback()
    return render_template('index.html', feedbacks=feedbacks)

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        course = request.form.get('course', '').strip()
        rating = request.form.get('rating', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not message:
            flash('Name and feedback message are required!', 'error')
            return render_template('feedback.html')

        add_feedback(name, course, rating, message)
        flash('Feedback submitted successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('feedback.html')

@app.route('/health')
def health():
    return {'status': 'ok', 'message': 'Student Feedback System is running'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
