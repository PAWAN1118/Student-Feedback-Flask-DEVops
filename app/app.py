from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from app.database import (
    init_db, add_feedback, get_all_feedback,
    delete_feedback, update_feedback, get_feedback_by_id,
    search_feedback, get_stats, get_paginated_feedback
)

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = 'student-feedback-secret-key'

init_db()

# ── Pages ──────────────────────────────────────────────────────────

@app.route('/')
def index():
    page     = request.args.get('page', 1, type=int)
    query    = request.args.get('q', '').strip()
    per_page = 6

    if query:
        feedbacks = search_feedback(query)
        total     = len(feedbacks)
        # Paginate search results manually
        start     = (page - 1) * per_page
        feedbacks = feedbacks[start:start + per_page]
    else:
        feedbacks, total = get_paginated_feedback(page, per_page)

    total_pages = max(1, (total + per_page - 1) // per_page)
    stats       = get_stats()

    return render_template(
        'index.html',
        feedbacks=feedbacks,
        stats=stats,
        page=page,
        total_pages=total_pages,
        total=total,
        query=query
    )

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        course  = request.form.get('course', '').strip()
        rating  = request.form.get('rating', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not message:
            flash('Name and feedback message are required!', 'error')
            return render_template('feedback.html',
                                   form_data=request.form)

        add_feedback(name, course, rating, message)
        flash('Feedback submitted successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('feedback.html', form_data={})

@app.route('/edit/<int:feedback_id>', methods=['GET', 'POST'])
def edit(feedback_id):
    fb = get_feedback_by_id(feedback_id)
    if not fb:
        flash('Feedback not found.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        course  = request.form.get('course', '').strip()
        rating  = request.form.get('rating', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not message:
            flash('Name and feedback message are required!', 'error')
            return render_template('edit.html', fb=fb)

        update_feedback(feedback_id, name, course, rating, message)
        flash('Feedback updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit.html', fb=fb)

# ── API endpoints ──────────────────────────────────────────────────

@app.route('/delete/<int:feedback_id>', methods=['POST'])
def delete(feedback_id):
    delete_feedback(feedback_id)
    flash('Feedback deleted.', 'success')
    return redirect(url_for('index'))

@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

@app.route('/health')
def health():
    return {'status': 'ok', 'message': 'Student Feedback System is running'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
