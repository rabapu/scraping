from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import math
from app.models import get_berita_paginated, get_berita_by_id, update_berita_relevance, arsip_berita_by_ids, set_need_analysis, update_berita_analysis
from app.services.scraper import fetch_article_content
from app.services.ai import generate_relevance_with_deepseek
from app.forms import AnalysisForm  # form baru untuk analisis
from app.decorators import admin_required

berita_bp = Blueprint('berita', __name__)


@berita_bp.route('/', methods=['GET'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Jika user biasa, hanya tampilkan berita yang sudah dianalisis
    if current_user.role == 'admin':
        berita_list, total = get_berita_paginated(page, per_page, filter_analyzed=False)
    else:
        berita_list, total = get_berita_paginated(page, per_page, filter_analyzed=True)

    total_pages = math.ceil(total / per_page)
    return render_template('index.html', hasil=berita_list, page=page, total_pages=total_pages,
                           per_page=per_page, total_berita=total, user_role=current_user.role)

@berita_bp.route('/generate_relevance/<int:berita_id>', methods=['POST'])
@login_required
def generate_relevance_single(berita_id):
    page = request.args.get('page', 1)
    berita = get_berita_by_id(berita_id)
    if not berita:
        flash('Berita tidak ditemukan.', 'danger')
        return redirect(url_for('berita.index', page=page))

    konten = fetch_article_content(berita['link'])
    if not konten:
        flash('Gagal mengambil konten artikel.', 'danger')
        return redirect(url_for('berita.index', page=page))

    result = generate_relevance_with_deepseek(berita['judul'], konten)
    if result:
        update_berita_relevance(berita_id, result['score'], result['explanation'])
        flash(f'Skor relevansi: {result["score"]}%', 'success')
    else:
        flash('Gagal memproses AI. Coba lagi.', 'danger')

    return redirect(url_for('berita.index', page=page))

@berita_bp.route('/delete_berita', methods=['POST'])
@login_required
@admin_required
def delete_berita():
    berita_ids_str = request.form.get('berita_ids', '')
    if berita_ids_str:
        ids = [int(id) for id in berita_ids_str.split(',') if id.isdigit()]
        if ids:
            arsip = arsip_berita_by_ids(ids)
            flash(f'{arsip} berita berhasil diarsipkan.', 'success')
        else:
            flash('Tidak ada ID valid.', 'danger')
    else:
        flash('Tidak ada berita yang dipilih.', 'warning')
    return redirect(url_for('berita.index'))

@berita_bp.route('/mark_need_analysis/<int:berita_id>', methods=['POST'])
@login_required
@admin_required
def mark_need_analysis(berita_id):
    """Menandai berita perlu dianalisis."""
    set_need_analysis(berita_id, True)
    flash('Berita ditandai untuk dianalisis.', 'success')
    return redirect(request.referrer or url_for('berita.index'))

@berita_bp.route('/analysis/<int:berita_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_analysis(berita_id):
    """Halaman untuk mengisi/mengedit analisis manual."""
    berita = get_berita_by_id(berita_id)
    if not berita:
        flash('Berita tidak ditemukan.', 'danger')
        return redirect(url_for('berita.index'))

    form = AnalysisForm()

    if form.validate_on_submit():
        # Simpan analisis
        update_berita_analysis(berita_id, form.analysis_data.data, form.analysis_conclusion.data)
        set_need_analysis(berita_id, True)  # Tandai selesai
        flash('Analisis berhasil disimpan.', 'success')
        return redirect(url_for('berita.index', page=request.args.get('page', 1)))

    # Jika GET, isi form dengan data yang sudah ada (jika ada)
    if request.method == 'GET':
        if berita['analysis_data']:
            form.analysis_data.data = berita['analysis_data']
        if berita['analysis_conclusion']:
            form.analysis_conclusion.data = berita['analysis_conclusion']

    return render_template('analysis_form.html', form=form, berita=berita)