from utils.utils import get_db_connection
import bcrypt
import os
import sqlite3


def add_default_user():
    default_username = "admin"
    default_password = "123"
    hashed_password = bcrypt.hashpw(default_password.encode("utf-8"), bcrypt.gensalt())
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Add default users
        cursor.execute(
            "INSERT INTO User (user_id, username, group_id, hash_password, home_dir, permissions) VALUES (?, ?, ?, ?, ?, ?)",
            (
                1,
                default_username,
                1,
                hashed_password,
                "/shared/home/admin",
                "read,write,list",
            ),
        )
        cursor.execute(
            "INSERT INTO User (user_id, username, group_id, hash_password, home_dir, permissions) VALUES (?, ?, ?, ?, ?, ?)",
            (2, "user1", 2, hashed_password, "/shared/home/user1", "read,list"),
        )
        cursor.execute(
            "INSERT INTO User (user_id, username, group_id, hash_password, home_dir, permissions) VALUES (?, ?, ?, ?, ?, ?)",
            (3, "user2", 2, hashed_password, "/shared/home/user2", "read,list"),
        )

        # Add default groups
        cursor.execute(
            "INSERT INTO userGroup (group_id, group_name) VALUES (?, ?)",
            (1, "admin_group"),
        )
        cursor.execute(
            "INSERT INTO userGroup (group_id, group_name) VALUES (?, ?)",
            (2, "user_group"),
        )

        # Add default directories
        cursor.execute(
            "INSERT INTO FileOrDirectory (id, path, owner_id, group_id, owner_perms, group_perms, public_perms, parent_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (5, "./shared", 1, 1, "read,list,write", "read,list", "read", None),
        )
        cursor.execute(
            "INSERT INTO FileOrDirectory (id, path, owner_id, group_id, owner_perms, group_perms, public_perms, parent_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (6, "./shared/home", 1, 1, "read,list,write", "read,list", "read", None),
        )

        connection.commit()
        print("Default users, groups, and directories added successfully.")
    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error adding default data: {e}")
    finally:
        cursor.close()
        connection.close()




def authenticate(username, password,shared_dir="shared"):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT hash_password, home_dir, user_id,group_id FROM User WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user is None: 
            return None
        stored_hash = user["hash_password"]
        if stored_hash is None: 
            return None
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return {
                "current_dir": os.path.join(os.getcwd(), shared_dir),
                "authenticated": True,
                "id": user["user_id"],
                "home_dir": user["home_dir"],
                "group_id": user["group_id"]
            }

        return None
    
