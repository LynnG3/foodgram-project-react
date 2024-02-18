# praktikum_new_diplom

https://pollyfoodgram.serveblog.net
Суперюзер:
TestSuperuser@yandex.ru
пароль:
BonAppeti



ПЕРЕДЕЛАТЬ ПОД ТЕКУЩИЙ ПРОЕКТ


Дипломный проект, выполненный в рамках учебного курса Яндекс.Практикум
Проект Foodgram -.
Для аутентификации токен.
Работает со всеми модулями Yamdb: произведениями, категориями, жанрами, отзывами к произведениям и комментариями к отзывам.
Поддерживает методы GET, POST, PATCH, DELETE
Предоставляет данные в формате JSON
Аутентифицированным пользователям разрешено изменение и удаление своих отзывов и комментариев;
модераторам разрешено изменение и удаление любых отзывов и комментариев;
админам и суперюзеру разрешено добавление произведений, жанров, категорий, изменение и удаление всех объектов;
в остальных случаях пользователям доступ предоставляется только для чтения.

### Установка:

Клонировать репозиторий :

```
git@github.com:LynnG3/foodgram-project-react.git
```

```
cd api_yamdb
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source venv/bin/activate
```

Обновить pip, установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

После запуска проекта, по адресу http://127.0.0.1:8000/redoc/ будет доступна документация для API Yatube.  Документация представлена в формате Redoc.

### Заполнение базы данными из файлов csv:

Из корневой директории проекта (с manage.py) запустить команду:

```
python manage.py import_csv
```

В терминале должны появиться сообщения:

Данные из .../data/category.csv успешно загружены в базу данных
...
Данные из .../data/genre_title.csv успешно загружены в базу данных
Все данные успешно загружены в базу данных!

### Примеры запросов:

#### 1. Аутентификация:
##### /auth/signup/
Права доступа: Все.\
POST метод - регистрация нового пользователя\
Пример запроса:
```
{
  "email": "user@example.com",
  "username": "string"
}
```
Пример ответа:
```
{
  "email": "user@example.com",
  "username": "string"
}
```
##### /auth/token/
Права доступа: Все.\
POST метод - получение JWT-токена.\
Пример запроса:
```
{
  "username": "string",
  "confirmation_code": "string"
}
```
Пример ответа:
```
{
  "token": "string"
}
```

#### 2. Работа с пользователями:
##### /users/
Права доступа: Администратор.\
GET метод - получение списка всех пользователей.\
POST метод - создание нового пользователя.\

Пример ответа на GET запрос:
```
{
  "count": 0,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "username": "string",
      "email": "user@example.com",
      "first_name": "string",
      "last_name": "string",
      "bio": "string",
      "role": "user"
    }
  ]
}
```
Пример POST запроса:
```
{
  "username": "string",
  "email": "user@example.com",
  "first_name": "string",
  "last_name": "string",
  "bio": "string",
  "role": "user"
}
```
Пример ответа на POST запрос:
```
{
  "username": "string",
  "email": "user@example.com",
  "first_name": "string",
  "last_name": "string",
  "bio": "string",
  "role": "user"
}
```
##### /users/{username}/
Права доступа: Администратор.\
GET метод - получение информации о пользователе.\
PATCH метод - изменение профиля пользователя.\
DEL метод - удаление профиля пользователя.\

Пример PATCH запроса:
```
{
  "username": "string",
  "email": "user@example.com",
  "first_name": "string",
  "last_name": "string",
  "bio": "string",
  "role": "user"
}
```

Пример ответа на GET и PATCH запросы:
```
{
  "username": "string",
  "email": "user@example.com",
  "first_name": "string",
  "last_name": "string",
  "bio": "string",
  "role": "user"
}
```

##### /users/me/
Права доступа: Авторизованный пользователь.\
GET метод - получение информации о своём профиле.\
PATCH метод - изменение своего профиля.\

Пример PATCH запроса:
```
{
  "username": "string",
  "email": "user@example.com",
  "first_name": "string",
  "last_name": "string",
  "bio": "string"
}
```

Пример ответа на GET и PATCH запросы:
```
{
  "username": "string",
  "email": "user@example.com",
  "first_name": "string",
  "last_name": "string",
  "bio": "string",
  "role": "user"
}
```
#### 3. Категории:
##### /categories/
GET метод - получение списка всех категорий. Права доступа: Все.\
POST метод - создание новой категории. Права доступа: Администратор.\
Пример ответа на GET запрос:
```
{
  "count": 0,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "name": "string",
      "slug": "string"
    }
  ]
}
```
Пример POST запроса:
```
{
  "name": "string",
  "slug": "string"
}
```
Пример ответа на POST запрос:
```
{
  "name": "string",
  "slug": "string"
}
```
##### /categories/{slug}/
DEL метод - удаление категории. Права доступа: Администратор.\

#### 4. Жанры:
##### /genres/
GET метод - получение списка всех жанров. Права доступа: Все.\
POST метод - создание нового жанра. Права доступа: Администратор.\

Пример ответа на GET запрос:
```
{
  "count": 0,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "name": "string",
      "slug": "string"
    }
  ]
}
```
Пример POST запроса:
```
{
  "name": "string",
  "slug": "string"
}
```
Пример ответа на POST запрос:
```
{
  "name": "string",
  "slug": "string"
}
```
##### /categories/{slug}/
DEL метод - удаление жанра. Права доступа: Администратор.\

#### 5. Произведения:
##### /titles/
GET метод - получение списка всех произведений. Права доступа: Все.\
POST метод - создание нового произведения. Права доступа: Администратор.\

Пример ответа на GET запрос:
```
{
  "count": 0,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": 0,
      "name": "string",
      "year": 0,
      "rating": 0,
      "description": "string",
      "genre": [
        {
          "name": "string",
          "slug": "string"
        }
      ],
      "category": {
        "name": "string",
        "slug": "string"
      }
    }
  ]
}
```
Пример POST запроса:
```
{
  "name": "string",
  "year": 0,
  "description": "string",
  "genre": [
    "string"
  ],
  "category": "string"
}
```
Пример ответа на POST запрос:
```
{
  "id": 0,
  "name": "string",
  "year": 0,
  "rating": 0,
  "description": "string",
  "genre": [
    {
      "name": "string",
      "slug": "string"
    }
  ],
  "category": {
    "name": "string",
    "slug": "string"
  }
}
```
##### /titles/{title_id}/
GET метод - получение информации о произведении. Права доступа: Все.\
PATCH метод - изменение произведения. Права доступа: Администратор.\
DEL метод - удаление произведения. Права доступа: Администратор.\

Пример PATCH запроса:
```
{
  "name": "string",
  "year": 0,
  "description": "string",
  "genre": [
    "string"
  ],
  "category": "string"
}
```

Пример ответа на GET и PATCH запросы:
```
{
  "id": 0,
  "name": "string",
  "year": 0,
  "rating": 0,
  "description": "string",
  "genre": [
    {
      "name": "string",
      "slug": "string"
    }
  ],
  "category": {
    "name": "string",
    "slug": "string"
  }
}
```

#### 6. Отзывы:
##### /titles/{title_id}/reviews/
GET метод - получение списка всех отзывов. Права доступа: Все.\
POST метод - создание нового отзыва на произведение. Пользователь может оставить только один отзыв на одно произведение. Права доступа: Аутентифицированные пользователи.\

Пример ответа на GET запрос:
```
{
  "count": 0,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": 0,
      "text": "string",
      "author": "string",
      "score": 1,
      "pub_date": "2019-08-24T14:15:22Z"
    }
  ]
}
```
Пример POST запроса:
```
{
  "text": "string",
  "score": 1
}
```
Пример ответа на POST запрос:
```
{
  "id": 0,
  "text": "string",
  "author": "string",
  "score": 1,
  "pub_date": "2019-08-24T14:15:22Z"
}
```
##### /titles/{title_id}/reviews/{review_id}/
GET метод - получение информации об отзыве. Права доступа: Все.\
PATCH метод - изменение отзыва. Права доступа: Автор отзыва, модератор или администратор.\
DEL метод - удаление отзыва. Права доступа: Автор отзыва, модератор или администратор.\

Пример PATCH запроса:
```
{
  "text": "string",
  "score": 1
}
```

Пример ответа на GET и PATCH запросы:
```
{
  "id": 0,
  "text": "string",
  "author": "string",
  "score": 1,
  "pub_date": "2019-08-24T14:15:22Z"
}
```

#### 7. Комментарии:
##### /titles/{title_id}/reviews/{review_id}/comments/
GET метод - получение списка всех комментариев к отзыву по id. Права доступа: Все.\
POST метод - создание нового комментария к отзыву. Права доступа: Аутентифицированные пользователи.\

Пример ответа на GET запрос:
```
{
  "count": 0,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": 0,
      "text": "string",
      "author": "string",
      "pub_date": "2019-08-24T14:15:22Z"
    }
  ]
}
```
Пример POST запроса:
```
{
  "text": "string"
}
```
Пример ответа на POST запрос:
```
{
  "id": 0,
  "text": "string",
  "author": "string",
  "pub_date": "2019-08-24T14:15:22Z"
}
```
##### /titles/{title_id}/reviews/{review_id}/comments/{comment_id}/
GET метод - получение информации о комментарии. Права доступа: Все.\
PATCH метод - изменение комментария. Права доступа: Автор комментария, модератор или администратор.\
DEL метод - удаление комментария. Права доступа: Автор комментария, модератор или администратор.\

Пример PATCH запроса:
```
{

}
```

Пример ответа на GET и PATCH запросы:
```
{

}
```

### Технологический стек проекта:
Проект написан на Python 3.9 с использованием DjangoRestFramework 3.12.4
Подключена библиотека Djoser для работы с токеном;
Для фильтрации данных применен модуль django-filter
Тестирование: flake8
Система управления версиями - git

### Об авторe:
Студентка 69 когорты курса 'Python-разработчик' Яндекс.Практикум 
Полина Грунина
