# yatube_project
### Описание
Социальная сеть Yatube с авторизацией, персональными лентами, комментариями и подпиской на авторов.
Докрутил лайки.
### Технологии
Python 3.7  
Django 2.2.19  
Unittest  
HTML  
SQLite3  
### Запуск проекта в dev-режиме
- Клонируйте репозиторий и перейти в него:
```
git clone git@github.com:dimabaril/yatube_final.git
cd yatube_final
```
- Создайте и активируйте виртуальное окружение:
```
python3 -m venv venv
source venv/bin/activate
```
- Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
``` 
- Выполните миграции:
```
cd yatube
python3 manage.py migrate
```
- Запустите проект:
```
python3 manage.py runserver
```
### Авторы
Барилкин Дмитрий
