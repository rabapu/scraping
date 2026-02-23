"""
User Service Module
Handles business logic for user management operations
"""
import pymysql
from app.utils.db import get_db_connection
from app.models import User
from pymysql.cursors import DictCursor


class UserService:
    """Service class for user-related operations"""
    
    @staticmethod
    def get_user_list(page=1, per_page=10):
        """
        Retrieve paginated list of users
        
        Args:
            page (int): Current page number (1-indexed)
            per_page (int): Number of users per page
            
        Returns:
            tuple: (users_list, total_users, total_pages)
        """
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
        return users, total, total_pages
    
    @staticmethod
    def get_user_by_id(user_id):
        """
        Get user details by ID
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict or None: User details
        """
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        cursor.execute("""
            SELECT id, username, email, role, created_at 
            FROM users 
            WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    
    @staticmethod
    def create_user(username, email, password, role='user'):
        """
        Create a new user
        
        Args:
            username (str): Username
            email (str): Email address
            password (str): User password (will be hashed)
            role (str): User role (default: 'user')
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            pymysql.IntegrityError: If username or email already exists
        """
        try:
            User.create(username, email, password, role)
            return True
        except pymysql.IntegrityError:
            raise ValueError("Username atau email sudah terdaftar")
        except Exception as e:
            raise Exception(f"Error membuat user: {str(e)}")
    
    @staticmethod
    def update_user(user_id, username=None, email=None, password=None, role=None):
        """
        Update user information
        
        Args:
            user_id (int): User ID to update
            username (str, optional): New username
            email (str, optional): New email
            password (str, optional): New password
            role (str, optional): New role
            
        Returns:
            bool: True if successful
        """
        try:
            User.update_by_id(user_id, username, email, password, role)
            return True
        except pymysql.IntegrityError:
            raise ValueError("Username atau email sudah terdaftar")
        except Exception as e:
            raise Exception(f"Error mengupdate user: {str(e)}")
    
    @staticmethod
    def delete_user(user_id):
        """
        Delete a user
        
        Args:
            user_id (int): User ID to delete
            
        Returns:
            bool: True if successful
        """
        try:
            User.delete_by_id(user_id)
            return True
        except Exception as e:
            raise Exception(f"Error menghapus user: {str(e)}")
    
    @staticmethod
    def count_users_by_role(role=None):
        """
        Count users by role
        
        Args:
            role (str, optional): Specific role to count. If None, returns all counts.
            
        Returns:
            dict or int: User count by role or specific count
        """
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        if role:
            cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = %s", (role,))
            result = cursor.fetchone()['total']
        else:
            cursor.execute("""
                SELECT role, COUNT(*) as count 
                FROM users 
                GROUP BY role
            """)
            result = {row['role']: row['count'] for row in cursor.fetchall()}
        
        cursor.close()
        conn.close()
        return result
    
    @staticmethod
    def search_users(search_term):
        """
        Search users by username or email
        
        Args:
            search_term (str): Search term
            
        Returns:
            list: List of matching users
        """
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        search_pattern = f"%{search_term}%"
        cursor.execute("""
            SELECT id, username, email, role, created_at 
            FROM users 
            WHERE username LIKE %s OR email LIKE %s
            ORDER BY created_at DESC
        """, (search_pattern, search_pattern))
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return users
    
    @staticmethod
    def get_user_activity_stats():
        """
        Get user-related statistics
        
        Returns:
            dict: Statistics about users
        """
        conn = get_db_connection()
        cursor = conn.cursor(DictCursor)
        
        # Total users
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()['total']
        
        # Users by role
        cursor.execute("""
            SELECT role, COUNT(*) as count 
            FROM users 
            GROUP BY role
        """)
        users_by_role = {row['role']: row['count'] for row in cursor.fetchall()}
        
        # Recently created users
        cursor.execute("""
            SELECT id, username, email, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 5
        """)
        recent_users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            'total_users': total_users,
            'users_by_role': users_by_role,
            'recent_users': recent_users
        }
