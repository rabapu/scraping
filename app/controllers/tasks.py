from flask import Blueprint, redirect, url_for, flash, render_template, jsonify
from flask_login import login_required
from app.decorators import admin_required
from app.models import get_all_keywords
from app.services.task_manager import generate_task_id, run_scrape_task, get_task_status
import threading

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/scrape', methods=['POST'])
@login_required
@admin_required
def start_scrape():
    keywords = get_all_keywords()
    if not keywords:
        flash('Tidak ada keyword. Silakan tambahkan keyword terlebih dahulu.', 'warning')
        return redirect(url_for('keywords.keywords'))

    task_id = generate_task_id()
    thread = threading.Thread(target=run_scrape_task, args=(task_id, keywords), daemon=True)
    thread.start()
    return redirect(url_for('tasks.loading_page', task_id=task_id))

@tasks_bp.route('/loading/<task_id>')
@login_required
@admin_required
def loading_page(task_id):
    task = get_task_status(task_id)
    if not task:
        flash('Task tidak ditemukan.', 'danger')
        return redirect(url_for('berita.index'))
    return render_template('loading.html', task_id=task_id)

@tasks_bp.route('/status/<task_id>')
@login_required
@admin_required
def task_status(task_id):
    task = get_task_status(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)