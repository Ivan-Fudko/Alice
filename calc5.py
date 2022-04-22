from flask import Flask, request

import logging
import json
from data import db_session
from data.stations import Station
from data.systems import System


app = Flask(__name__)

app.run
db_session.global_init("db/system_db.sqlite")
db_sess = db_session.create_session()


logging.basicConfig(level=logging.INFO)
t = 0
pilot_sistem = 0
services = []

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():

    logging.info(f'Request: {request.json!r}')

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(request.json, response)

    logging.info(f'Response:  {response!r}')
    return json.dumps(response)


def handle_dialog(req, res):
    user_id = req['session']['user_id']
    global t, pilot_sistem, services
    if req['session']['new']:

        sessionStorage[user_id] = {
            'services': [
                'Заправка',
                'Ремонт',
                'Рынок',
                'Пополнение боезапаса',
                'Поиск'],
            }
        res['response']['text'] = 'Здравствуйте Капитан. Введите пожалуйста систему в которой находите.'
        return
    session = sessionStorage[user_id]
    if req['request']['original_utterance'].capitalize() in session['services']:
        session['services'].remove(req['request']['original_utterance'].capitalize())

    if req['request']['original_utterance'].lower() == 'поиск':
        services.remove(pilot_sistem)
        systems_id = []
        nearest_sistem = ''
        nearest_sistem_id = 0
        min_range = 10 ** 10
        pilot_system_id = db_sess.query(System.id).filter(System.name == pilot_sistem).first()[0]
        pilot_system_cord = db_sess.query(System.cord_x, System.cord_y, System.cord_z).filter(System.name == pilot_sistem).first()
        search = ''
        for i in services:
            if i == 'заправка':
                search += '2'
            if i == 'ремонт':
                search += '4'
            if i == 'рынок':
                search += '1'
            if i == 'пополнение боезапаса':
                search += '3'
        if db_sess.query(Station.name).filter(Station.system_id == pilot_system_id, Station.services.like(f'%{search}%')).first():
            station_name = db_sess.query(Station.name).filter(Station.id == pilot_system_id,
                                                              Station.services.like(f'%{search}%')).first()
            res['response']['text'] = f'Нужная вам станция под названием {station_name[0]} находится в системе {pilot_sistem}'
            res['response']['end_session'] = True
            return
        else:
            for id in db_sess.query(Station.system_id).filter(Station.services.like(f'%{search}%')).all():
                system_cords = db_sess.query(System.cord_x, System.cord_y, System.cord_z).filter(System.id == id[0]).first()
                range = round(((pilot_system_cord[0] - system_cords[0]) ** 2 + (pilot_system_cord[1] - system_cords[1]) ** 2 +
                         (pilot_system_cord[2] - system_cords[2]) ** 2) ** 0.5)
                if range < min_range:
                    min_range = range
                    nearest_sistem_id = id[0]
            nearest_sistem = db_sess.query(System.name).filter(System.id == nearest_sistem_id).first()[0]
            station_name = db_sess.query(Station.name).filter(Station.system_id == nearest_sistem_id,
                                                              Station.services.like(f'%{search}%')).first()[0]
            res['response'][
                'text'] = f'Нужная вам станция под названием {station_name} находится в системе {nearest_sistem} ' \
                          f'на растояние в {min_range} световы лет.'
            res['response']['end_session'] = True
            return

    if pilot_sistem == 0:
        pilot_sistem = req['request']['original_utterance'].lower()
    if db_sess.query(System.id).filter(System.name.like(f'%{pilot_sistem}%')).first():
        if t == 1:
            res['response']['text'] = 'Что-нибудь ещё?'
            res['response']['buttons'] = get_suggests(user_id)
            services.append(req['request']['original_utterance'].lower())
            return
        if t == 0:
            res['response']['text'] = 'Пожалуйтса выберите услуги.'
            res['response']['buttons'] = get_suggests(user_id)
            t = 1
            services.append(req['request']['original_utterance'].lower())
            return

    else:
        pilot_sistem = 0
        res['response']['text'] = 'Извините ,но такой системы нет в базе'


def get_suggests(user_id):
    session = sessionStorage[user_id]
    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['services']
    ]

    return suggests


def get_picture(user_id):
    pass


if __name__ == '__main__':
    app.run()