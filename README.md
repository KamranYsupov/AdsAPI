<h1>Запуск проекта</h1>

<h4>
1. Создайте файл .env в корневой директории 
проекта и установите переменные согласно .env.example:
</h4>

```requirements
PROJECT_NAME=
SECRET_KEY=
DEBUG=

DB_NAME=<Название БД>
DB_USER=<Пользователь БД>
DB_PASSWORD=<Пароль от БД>
DB_HOST=db
DB_PORT=5432
```

<h4>
2. Запустите docker compose:
</h4>

```commandline
docker compose up --build -d
```


<h4>
3. Создайте суперпользователя админ панели:
</h4>

```commandline
docker exec -it {PROJECT_NAME из .env}_web python manage.py createsuperuser
```
<br>
<h4>
Готово! Главная страница доступна по адресу http://127.0.0.1
</h4>

