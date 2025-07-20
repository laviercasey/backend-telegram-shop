import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

def create_database_backup(db_name, output_dir):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(output_dir, f"{db_name}_{timestamp}.sql")
    
    try:
        subprocess.run(
            ["pg_dump", "-U", "postgres", "-d", db_name, "-f", backup_file],
            check=True
        )
        print(f"Резервная копия базы данных создана: {backup_file}")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при создании резервной копии: {e}")

if __name__ == "__main__":
    backup_dir = os.path.join(Path(__file__).parent.parent, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    db_name = os.environ.get("POSTGRES_DB", "telegram_shop")
    
    create_database_backup(db_name, backup_dir)
