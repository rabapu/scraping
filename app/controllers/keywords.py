from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.forms import KeywordForm
from app.models import get_keywords_with_details, add_keyword, delete_keyword_by_id
from app.decorators import admin_required

keywords_bp = Blueprint('keywords', __name__)

@keywords_bp.route('/keywords', methods=['GET', 'POST'])
@login_required
@admin_required
def keywords():
    form = KeywordForm()
    if form.validate_on_submit():
        keyword = form.keyword.data.strip().lower()
        try:
            add_keyword(keyword)
            flash(f'Keyword "{keyword}" berhasil ditambahkan.', 'success')
        except ValueError as e:
            flash(str(e), 'danger')
        return redirect(url_for('keywords.keywords'))

    keywords_list = get_keywords_with_details()
    return render_template('keywords.html', form=form, keywords=keywords_list)

@keywords_bp.route('/keywords/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_keyword(id):
    delete_keyword_by_id(id)
    flash('Keyword dihapus.', 'success')
    return redirect(url_for('keywords.keywords'))