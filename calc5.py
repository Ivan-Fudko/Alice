from flask import Flask, request

import logging
import json
from data import db_session
from data.stations import Station
from data.systems import System



app = Flask(__name__)

app.run
db_session.global_init("db/system_db.db")
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