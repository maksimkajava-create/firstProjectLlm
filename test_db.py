from database.connection import SessionLocal
from models.entities import MLModelConfig, MLTask, User
from services.crud.ml_task import get_user_history
from services.crud.user import process_transaction

def run_tests():
    db = SessionLocal()
    try:
        print("--- тестирование ---")

        # 1. Загрузка пользователя из БД
        user = db.query(User).filter(User.email == "demo@mail.ru").first()
        print(f"1. Загружен пользователь: {user.email}, Баланс: {user.balance}")

        # 2. Пополнение баланса
        process_transaction(db, user=user, amount=50.0, t_type="credit")
        print(f"2. Баланс после пополнения на 50: {user.balance}")

        # 3. Эмуляция ML-запроса
        model = db.query(MLModelConfig).filter(MLModelConfig.name == "SimpleClassifier").first()
        cost = model.cost_per_prediction

        print(f"3. Стоимость предсказания: {cost}. Проверка баланса...")
        if user.balance >= cost:
            # Запись о задаче 
            task = MLTask(
                user_id=user.id,
                model_id=model.id,
                input_data={"features": [1, -2, 3]},
                output_data={"label": "A"},
                status="completed"
            )
            db.add(task)
            db.flush() 

            # Списание баланса
            process_transaction(db, user=user, amount=cost, t_type="debit", task_id=task.id)
            print("   Списание прошло успешно, задача сохранена.")
        else:
            print("   Недостаточно средств!")

        # 4. Проверка баланса перед списанием 
        print("4. Проверка списания при нехватке средств...")
        try:
            process_transaction(db, user=user, amount=9999.0, t_type="debit")
        except ValueError as e:
            print(f"Ожидаемая ошибка: {e}")

        # 5. История запросов пользователя
        print("5. История ML-запросов пользователя по дате:")
        history = get_user_history(db, user.id)

        for idx, h_task in enumerate(history, start=1):
            # Сумма списания из связанной таблицы транзакций
            txn_amount = h_task.transaction.amount if h_task.transaction else "Нет данных"
            print(f"   {idx}. Запрос от {h_task.created_at.strftime('%Y-%m-%d %H:%M:%S')} | "
                  f"Модель: {h_task.model.name} | "
                  f"Вход: {h_task.input_data} -> Выход: {h_task.output_data} | "
                  f"Стоило: {txn_amount}")

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()