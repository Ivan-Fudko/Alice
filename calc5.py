from flask import Flask, request

import logging
import json
from data import db_session
from data.stations import Station
from data.systems import System
from data.jaro import jaro_winkler


app = Flask(__name__)

app.run
db_session.global_init("db/system_db.sqlite")
db_sess = db_session.create_session()


logging.basicConfig(level=logging.INFO)

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
    if req['session']['new']:

        sessionStorage[user_id] = {
            'services': [
                'Заправка',
                'Ремонт',
                'Рынок',
                'Пополнение боезапаса',
                'Поиск'],
            'services_search': [],
            'pilot_system': 0,
            't': 0,
            'systems_and_percent': {},
            'possible_systems': []
            }
        res['response']['text'] = 'Здравствуйте Капитан. '
        return
    session = sessionStorage[user_id]

    if req['request']['original_utterance'].capitalize() in session['services']:
        session['services'].remove(req['request']['original_utterance'].capitalize())

    if req['request']['original_utterance'].lower() == 'поиск':
        session['services_search'].remove(session['pilot_system'])
        nearest_system_id = 0
        min_range = 10 ** 10
        pilot_system_id = db_sess.query(System.id).filter(System.name == session['pilot_system']).first()[0]
        pilot_system_cord = db_sess.query(System.cord_x, System.cord_y,
                                          System.cord_z).filter(System.name == session['pilot_system']).first()
        search = []
        for i in session['services_search']:
            if i == 'заправка':
                search.append('2')
            if i == 'ремонт':
                search.append('4')
            if i == 'рынок':
                search.append('1')
            if i == 'пополнение боезапаса':
                search.append('3')
        search.sort()
        search = ''.join(search)
        if db_sess.query(Station.name).filter(Station.system_id == pilot_system_id, Station.services.like(f'%{search}%')).first():
            station_name = db_sess.query(Station.name).filter(Station.system_id == pilot_system_id,
                                                              Station.services.like(f'%{search}%')).first()
            res['response']['text'] = f'Нужная вам станция под названием {station_name[0]} находится в той же ' \
                                      f'системе,что и вы.'

            res['response']['end_session'] = True
            return
        else:
            for id in db_sess.query(Station.system_id).filter(Station.services.like(f'%{search}%')).all():
                system_cords = db_sess.query(System.cord_x, System.cord_y, System.cord_z).filter(System.id == id[0]).first()
                range = round(((pilot_system_cord[0] - system_cords[0]) ** 2 + (pilot_system_cord[1] - system_cords[1]) ** 2 +
                         (pilot_system_cord[2] - system_cords[2]) ** 2) ** 0.5)
                if range < min_range:
                    min_range = range
                    nearest_system_id = id[0]
            nearest_system = db_sess.query(System.name).filter(System.id == nearest_system_id).first()[0]
            station_name = db_sess.query(Station.name).filter(Station.system_id == nearest_system_id,
                                                              Station.services.like(f'%{search}%')).first()[0]
            res['response'][
                'text'] = f'Нужная вам станция под названием {station_name} находится в системе {nearest_system} ' \
                          f'на растояние в {min_range} световы лет.'
            res['response']['end_session'] = True
            return

    if session['pilot_system'] == 0:
        session['pilot_system'] = req['request']['original_utterance'].lower()
    if db_sess.query(System.id).filter(System.name == session["pilot_system"]).first():
        if session['t'] == 1:
            res['response']['text'] = 'Что-нибудь ещё?'
            res['response']['buttons'] = get_suggests(user_id, 'serv')
            session['services_search'].append(req['request']['original_utterance'].lower())
            return
        if session['t'] == 0:
            res['response']['text'] = 'Пожалуйтса выберите услуги.'
            res['response']['buttons'] = get_suggests(user_id, 'serv')
            session['t'] = 1
            session['services_search'].append(req['request']['original_utterance'].lower())
            return

    else:
        res['response']['text'] = 'Извините ,но такой системы нет в базе.'
        res['response']['text'] = 'Возможно вы имели в виду что-то из этого.'
        all_systems = db_sess.query(System.name).all()
        for system in all_systems:
            session['systems_and_percent'][system[0]] = jaro_winkler(session['pilot_system'], system[0])
        sorted_values = sorted(session['systems_and_percent'].values(), reverse=True)  # Sort the values
        sorted_dict = {}
        for i in sorted_values:
            for k in session['systems_and_percent'].keys():
                if session['systems_and_percent'][k] == i:
                    sorted_dict[k] = session['systems_and_percent'][k]
                    break
        for k, v in sorted_dict.items():
            if len(session['possible_systems']) != 5:
                session['possible_systems'].append(k)
            else:
                break
        res['response']['buttons'] = get_suggests(user_id, 'syst')
        session['pilot_system'] = 0
        return


def get_suggests(user_id, type):
    if type == 'serv':
        session = sessionStorage[user_id]
        suggests = [
            {'title': suggest, 'hide': True}
            for suggest in session['services']
        ]
    elif type == 'syst':
        session = sessionStorage[user_id]
        suggests = [
            {'title': suggest, 'hide': True}
            for suggest in session['possible_systems']
        ]
    return suggests


if __name__ == '__main__':
    app.run()