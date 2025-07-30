import sqlite3
import os

# Veritabanı dosyasının yolunu doğru ayarladığınızdan emin olun
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'lezzet_defteri.db')

def sync_categories():
    print("Veritabanına bağlanılıyor...")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. 'recipes' tablosundaki mevcut, benzersiz ve boş olmayan tüm kategorileri al
    cursor.execute("SELECT DISTINCT kategori FROM recipes WHERE kategori IS NOT NULL AND kategori != '' AND kategori != 'Kategorisiz'")
    existing_categories_in_recipes = [row['kategori'] for row in cursor.fetchall()]

    if not existing_categories_in_recipes:
        print("Aktarılacak mevcut tarif kategorisi bulunamadı.")
        conn.close()
        return

    print(f"Tariflerinizde {len(existing_categories_in_recipes)} adet benzersiz kategori bulundu:")
    print(existing_categories_in_recipes)

    # 2. Bu kategorileri yeni 'categories' tablosuna ekle
    count = 0
    for category_name in existing_categories_in_recipes:
        try:
            # Kategorinin zaten 'categories' tablosunda olup olmadığını kontrol et
            cursor.execute("SELECT name FROM categories WHERE name = ?", (category_name,))
            if cursor.fetchone() is None:
                # Eğer yoksa ekle
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
                count += 1
            else:
                print(f"-> '{category_name}' kategorisi zaten yönetim tablosunda mevcut, atlanıyor.")
        except sqlite3.IntegrityError:
            # Bu hata normalde yukarıdaki kontrolle engellenir ama garanti olsun diye var
            print(f"-> '{category_name}' zaten var, atlanıyor.")
            pass

    conn.commit()
    conn.close()

    print(f"\nİşlem tamamlandı! {count} adet yeni kategori, 'Kategorileri Yönet' bölümüne başarıyla eklendi.")

if __name__ == '__main__':
    sync_categories()