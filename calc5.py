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
            'services_add': [
                'Заправка',
                'Ремонт',
                'Рынок',
                'Пополнение боезапаса',
                'Добавить'],
            'services_search': [],
            'pilot_system': 0,
            't': 0,
            'systems_and_percent': {},
            'possible_systems': [],
            'find_or_add': [
                'найти станцию',
                'добавить данные'],
            'find': 0,
            'system_or_station': [
                'добавить станцию',
                'добавить систему'
            ],
            'add_system': 0,
            'add_station': 0,
            'new_system_name': 0,
            'new_cords': 0,
            'input_system_words': 1,
            'input_cord_words': 1,
            'system_for_stations': '',
            'input_station_words': 1,
            'input_services_words': 1,
            'new_station_name': '',
            'a': 0
            }
        res['response']['text'] = 'Здравствуйте Капитан. Что вы хотите сделать сеегодня?'
        res['response']['buttons'] = get_suggests(user_id, 'find_or_add')
        return
    session = sessionStorage[user_id]
    if req['request']['original_utterance'].lower() == 'добавить данные':
        res['response']['text'] = 'Что вы хотите добавить станции или систему?'
        res['response']['buttons'] = get_suggests(user_id, 'system_or_station')
        return

    if req['request']['original_utterance'].lower() == 'добавить систему' or session['add_system']:
        session['add_system'] = 1
        if not session['new_system_name'] and session['input_system_words']:
            res['response']['text'] = 'Введити название новой системы'
            session['input_system_words'] = 0
            return
        elif not session['input_system_words'] and not session['new_system_name']:
            session['new_system_name'] = req['request']['original_utterance'].lower()
        if not session['new_cords'] and session['input_cord_words']:
            res['response']['text'] = 'Введити координаты в формате x.y.z'
            session['input_cord_words'] = 0
            return
        elif not session['input_cord_words'] and not session['new_cords']:
            session['new_cords'] = req['request']['original_utterance'].lower()
            if len(req['request']['nlu']['tokens']) == 3:
                try:
                    splited_cords = session['new_cords'].split('.')
                    for i in splited_cords:
                        a = int(i)
                except ValueError:
                    res['response']['text'] = 'Не правельный формат координат.'
                    session['new_cords'] = 0
                    return
                system = System()
                system.name = session['new_system_name']
                system.cord_x = session['new_cords'].split('.')[0]
                system.cord_y = session['new_cords'].split('.')[1]
                system.cord_z = session['new_cords'].split('.')[2]
                db_sess.add(system)
                db_sess.commit()
                res['response']['text'] = 'Система успешно добавлена.'
                res['response']['end_session'] = True
            else:
                res['response']['text'] = 'Не правельный формат координат.'
                session['new_cords'] = 0
                return
    if req['request']['original_utterance'].lower() == 'добавить станцию' or session['add_station']:
        session['add_station'] = 1
        if not session['system_for_stations'] and session['input_system_words']:
            res['response']['text'] = 'Введити название системы'
            session['input_system_words'] = 0
            return
        elif not session['input_system_words'] and not session['system_for_stations']:
            session['system_for_stations'] = req['request']['original_utterance'].lower()
            if db_sess.query(System.id).filter(System.name == session["system_for_stations"]).first():
                pass
            else:
                res['response']['text'] = 'Извините ,но такой системы нет в базе.' \
                                          'Возможно вы имели в виду что-то из этого.'
                all_systems = db_sess.query(System.name).all()
                for system in all_systems:
                    session['systems_and_percent'][system[0]] = jaro_winkler(session['system_for_stations'], system[0])
                sorted_values = sorted(session['systems_and_percent'].values(), reverse=True)
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
                res['response']['buttons'] = get_suggests(user_id, 'possible_systems')
                session['system_for_stations'] = ''
                return
        if req['request']['original_utterance'].lower() == 'добавить':
            session['services_search'].remove(session['new_station_name'])
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
            station = Station()
            station.name = session['new_station_name']
            station.system_id = db_sess.query(System.id).filter(System.name == session['system_for_stations']).first()[
                0]
            station.services = search
            db_sess.add(station)
            db_sess.commit()
            res['response']['text'] = 'Станция успешно добавлена.'
            res['response']['end_session'] = True
            return
        if not session['new_station_name'] and session['input_station_words']:
            res['response']['text'] = 'Введити название новой станции'
            session['input_station_words'] = 0
            return
        elif not session['input_station_words'] and not session['new_station_name']:
            if session['a'] == 0:
                session['a'] += 1
                pass
            else:
                session['a'] += 1
                pass
            session['new_station_name'] = req['request']['original_utterance'].lower()
            system_id = db_sess.query(System.id).filter(System.name == session["system_for_stations"]).first()
            print(system_id)
            print(db_sess.query(Station.id).filter(Station.system_id == system_id[0], Station.name == session['new_station_name']).first())
            if db_sess.query(Station.id).filter(Station.system_id == system_id[0],
                                                Station.name == session['new_station_name']).first():
                res['response']['text'] = f'В системе {session["system_for_stations"]} уже есть станция с ' \
                                          f'таким названием.'
                session['new_station_name'] = ''
                return
        if req['request']['original_utterance'].capitalize() in session['services']:
            session['services_add'].remove(req['request']['original_utterance'].capitalize())
        if session['t'] == 1:
            res['response']['text'] = 'Что-нибудь ещё?'
            res['response']['buttons'] = get_suggests(user_id, 'services_add')
            session['services_search'].append(req['request']['original_utterance'].lower())
            return
        if session['t'] == 0:
            res['response']['text'] = 'Пожалуйтса выберите услуги.'
            res['response']['buttons'] = get_suggests(user_id, 'services_add')
            session['t'] = 1
            session['services_search'].append(req['request']['original_utterance'].lower())
            return


    if req['request']['original_utterance'].lower() == 'найти станцию':
        session['find'] = 1
        res['response']['text'] = 'Введите пожалуйста систему в которой находите.'
        return

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
            search_dict = []
            if len(search) == 1:
                search_dict = db_sess.query(Station.system_id).filter(Station.services.like(f'%{search}%')).all()
            elif len(search) == 2:
                search_dict = db_sess.query(Station.system_id).filter(Station.services.like(f'%{search[0]}%'),
                                                                      Station.services.like(f'%{search[1]}%')).all()
            elif len(search) == 3:
                search_dict = db_sess.query(Station.system_id).filter(Station.services.like(f'%{search[0]}%'),
                                                                      Station.services.like(f'%{search[1]}%'),
                                                                      Station.services.like(f'%{search[2]}%')).all()
            else:
                search_dict = db_sess.query(Station.system_id).filter(Station.services.like(f'%{search[0]}%'),
                                                                      Station.services.like(f'%{search[1]}%'),
                                                                      Station.services.like(f'%{search[2]}%'),
                                                                      Station.services.like(f'%{search[3]}%')).all()
            for id in search_dict:
                system_cords = db_sess.query(System.cord_x, System.cord_y, System.cord_z).filter(System.id == id[0]).first()
                range1 = round(((pilot_system_cord[0] - system_cords[0]) ** 2 + (pilot_system_cord[1] - system_cords[1]) ** 2 +
                         (pilot_system_cord[2] - system_cords[2]) ** 2) ** 0.5)
                if range1 < min_range:
                    min_range = range1
                    nearest_system_id = id[0]
            nearest_system = db_sess.query(System.name).filter(System.id == nearest_system_id).first()[0]
            if len(search) == 1:
                station_name = db_sess.query(Station.name).filter(Station.system_id == nearest_system_id,
                                                                  Station.services.like(f'%{search[0]}%')).first()[0]
            elif len(search) == 2:
                station_name = db_sess.query(Station.name).filter(Station.system_id == nearest_system_id,
                                                                  Station.services.like(f'%{search[0]}%'),
                                                                  Station.services.like(f'%{search[1]}%')).first()[0]
            elif len(search) == 3:
                station_name = db_sess.query(Station.name).filter(Station.system_id == nearest_system_id,
                                                                  Station.services.like(f'%{search[0]}%'),
                                                                  Station.services.like(f'%{search[1]}%'),
                                                                  Station.services.like(f'%{search[2]}%')).first()[0]
            else:
                station_name = db_sess.query(Station.name).filter(Station.system_id == nearest_system_id,
                                                                  Station.services.like(f'%{search[0]}%'),
                                                                  Station.services.like(f'%{search[1]}%'),
                                                                  Station.services.like(f'%{search[2]}%'),
                                                                  Station.services.like(f'%{search[3]}%')).first()[0]
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
            res['response']['buttons'] = get_suggests(user_id, 'services')
            session['services_search'].append(req['request']['original_utterance'].lower())
            return
        if session['t'] == 0:
            res['response']['text'] = 'Пожалуйтса выберите услуги.'
            res['response']['buttons'] = get_suggests(user_id, 'services')
            session['t'] = 1
            session['services_search'].append(req['request']['original_utterance'].lower())
            return

    elif session['find']:
        res['response']['text'] = 'Извините ,но такой системы нет в базе.'
        res['response']['text'] = 'Возможно вы имели в виду что-то из этого.'
        all_systems = db_sess.query(System.name).all()
        for system in all_systems:
            session['systems_and_percent'][system[0]] = jaro_winkler(session['pilot_system'], system[0])
        sorted_values = sorted(session['systems_and_percent'].values(), reverse=True)
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
        res['response']['buttons'] = get_suggests(user_id, 'possible_systems')
        session['pilot_system'] = 0
        return


def get_suggests(user_id, buttons):
    session = sessionStorage[user_id]
    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session[buttons]
    ]

    return suggests


if __name__ == '__main__':
    app.run()