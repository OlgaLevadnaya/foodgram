**Описание проекта:**

Проект «Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

---

**Технологии:**

- Python v. 3.9,
- Django v. 3.2.3,
- djangorestframework 3.12.4.

---

**Проект состоит из следующих страниц:**
- главная,
- страница входа,
- страница регистрации,
- страница рецепта,
- страница пользователя,
- страница подписок,
- избранное,
- список покупок,
- создание и редактирование рецепта,
- страница смены пароля.

---

**Как запустить проект:**

Находясь в папке infra, выполните команду sudo docker compose -f docker-compose-local.yml up. Локально приложение будет доступно по адресу: http://localhost:8080/, админ-зона по адресу http://localhost:8080/admin/.

Переменные окружения необходимо сохранить в файле .env, пример файла .env.example.

---

**Автор проекта:** Ольга Левадная (бэкенд)
