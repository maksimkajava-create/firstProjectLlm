from database.connection import Base, SessionLocal, engine
from models.entities import MLModelConfig, User
from services.crud.user import create_user

def init_db():
    print("Создаем таблицы в БД...")

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        demo_user = db.query(User).filter(User.email == "demo@mail.ru").first()
        if not demo_user:
            print("Создаем демо-пользователя...")
            create_user(db, email="demo@mail.ru", password="demo_password", balance=150.0)
        else:
            print("Демо-пользователь уже существует.")
            
        admin_user = db.query(User).filter(User.email == "admin@mail.ru").first()
        if not admin_user:
            print("Создаем администратора...")
            admin = create_user(db, email="admin@mail.ru", password="admin_password", balance=500.0)
            admin.role = "admin"
            db.commit()
        else:
            print("Администратор уже существует.")
            
        base_model = db.query(MLModelConfig).filter(MLModelConfig.name == "SimpleClassifier").first()
        if not base_model:
            print("Создаем демо ML-модель...")
            model = MLModelConfig(
                name="SimpleClassifier",
                description="Классификатор по сумме признаков",
                cost_per_prediction=15.0
            )
            db.add(model)
            db.commit()
        else:
            print("Демо ML-модель уже существует.")

    except Exception as e:
        print(f"Ошибка при инициализации БД: {e}")
        db.rollback()
    finally:
        db.close()
        print("Инициализация завершена.")

if __name__ == "__main__":
    init_db()