from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.decorators import admin_required
from app.forms import UserForm
from app.models import User
from app.utils.db import get_db_connection
from werkzeug.security import generate_password_hash
from pymysql.cursors import DictCursor
import pymysql

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    # Check if user is admin (optional - adjust based on your role system)
    #if current_user.role not in ['admin', 'superuser']:
    #    flash('Anda tidak memiliki izin untuk membuat user baru.', 'danger')
    #    return redirect(url_for('users.list_users'))
    
    form = UserForm()
    if form.validate_on_submit():
        try:
            User.create(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                role=form.role.data
            )
            flash(f'User {form.username.data} berhasil dibuat!', 'success')
            return redirect(url_for('users.list_users'))
        except pymysql.IntegrityError:
            flash('Username atau email sudah terdaftar.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('users/create.html', form=form)

# Read - List all users
@users_bp.route('/list', methods=['GET'])
@login_required
@admin_required
def list_users():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    conn = get_db_connection()
    cursor = conn.cursor(DictCursor)
    
    # Get total count
    cursor.execute("SELECT COUNT(*) as total FROM users")
    total = cursor.fetchone()['total']
    
    # Get paginated users
    offset = (page - 1) * per_page
    cursor.execute("""
        SELECT id, username, email, role, created_at 
        FROM users 
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    users = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('users/list.html', 
                         users=users, 
                         page=page, 
                         total_pages=total_pages,
                         total=total)

# Read - View single user details
@users_bp.route('/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def view_user(user_id):
    user = User.get(user_id)
    
    if not user:
        flash('User tidak ditemukan.', 'danger')
        return redirect(url_for('users.list_users'))
    
    # Get detailed user info from database
    conn = get_db_connection()
    cursor = conn.cursor(DictCursor)
    cursor.execute("""
        SELECT id, username, email, role, created_at 
        FROM users 
        WHERE id = %s
    """, (user_id,))
    user_details = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('users/detail.html', user=user_details)

# Update - Edit user
@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def update_user(user_id):
    user = User.get(user_id)
    
    if not user:
        flash('User tidak ditemukan.', 'danger')
        return redirect(url_for('users.list_users'))
    
    # Check permission - user dapat edit profil sendiri atau admin dapat edit user lain
    if current_user.id != user_id and current_user.role not in ['admin', 'superuser']:
        flash('Anda tidak memiliki izin untuk mengubah user ini.', 'danger')
        return redirect(url_for('users.view_user', user_id=user_id))
    
    form = UserForm()
    
    if form.validate_on_submit():
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Update basic info
            cursor.execute("""
                UPDATE users 
                SET username = %s, email = %s, role = %s
                WHERE id = %s
            """, (form.username.data, form.email.data, form.role.data, user_id))
            
            # Update password if provided
            if form.password.data:
                password_hash = generate_password_hash(form.password.data)
                cursor.execute("""
                    UPDATE users 
                    SET password_hash = %s
                    WHERE id = %s
                """, (password_hash, user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('User berhasil diperbarui!', 'success')
            return redirect(url_for('users.view_user', user_id=user_id))
        except pymysql.IntegrityError:
            flash('Username atau email sudah terdaftar.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role
    
    return render_template('users/edit.html', form=form, user=user)

# Delete - Remove user
@users_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    # Check if user is admin
    if current_user.role not in ['admin', 'superuser']:
        flash('Anda tidak memiliki izin untuk menghapus user.', 'danger')
        return redirect(url_for('users.list_users'))
    
    # Prevent deleting yourself
    if current_user.id == user_id:
        flash('Anda tidak dapat menghapus akun Anda sendiri.', 'danger')
        return redirect(url_for('users.view_user', user_id=user_id))
    
    user = User.get(user_id)
    if not user:
        flash('User tidak ditemukan.', 'danger')
        return redirect(url_for('users.list_users'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash(f'User {user.username} berhasil dihapus!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('users.list_users'))