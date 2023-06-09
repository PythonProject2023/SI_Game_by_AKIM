import asyncio
import shlex
from io import StringIO
import random
import copy
import locale
import os
import gettext

clients = {}
master = ''
password = 'password'

async def SIG(reader, writer):
    """Функция, реализуящая функциональности сервера.

    Организует запуск на выполнение принимаемых от пользователя команд,
    а также посылает ответы пользователю или широковещательные сообщения.
    """
    print("HERE WE GO")
    global clients, master, password
    to_login = asyncio.create_task(reader.readline())
    res = await to_login
    name = res.decode()[:-1]

    if len(clients) == 0:
        master = name

    if name in clients:
        writer.write(("sorry").encode())
        await writer.drain()
        return False
    else:
        writer.write(("hello").encode())
        await writer.drain()

    to_pass = asyncio.create_task(reader.readline())
    res = await to_pass
    if res == password:
        for cur_name in clients:
            await clients[cur_name].put(("{} has connected").format(name))
    else:
        writer.write(("sorry").encode())
        await writer.drain()
        return False
                
    clients[name] = asyncio.Queue()
##    print(name, 'connected')

    class cmd_holder:
        """служебный класс - держатель команд."""
        def __init__(self, func: callable, is_broadcast: bool):
            """инициализируем объект: кладем метод и информацию о broadcaste."""
            self.target = func
            self.broadcast = is_broadcast

        def get_target(self):
            """getter для получения метода."""
            return self.target

        def get_broadcast(self):
            """getter для получения информации о broadcaste."""
            return self.broadcast

    # словарь доступных команд и соотв. им методов класса Player
    ##available_cmds = {'move': cmd_holder(Player.move, False),
    ##                  'attack': cmd_holder(Player.attack, True),
    ##                  'addmon': cmd_holder(Player.init_monster, True),
    ##                  'sayall': cmd_holder(Player.say, True),
    ##                  'monsters': cmd_holder(Player.available_monsters, False),
    ##                  'locale': cmd_holder(Player.set_locale, False)
    ##                  }
    # заводим для клиента объект класса Player
    ##player = Player(name)

    # создаем два задания: на чтение и на запись
    send = asyncio.create_task(reader.readline())
    receive = asyncio.create_task(clients[name].get())
    global roamer

    while not reader.at_eof():
        # обрабатываем выполненные задания с учетом того, что они могут закончиться одновременно
        done, pending = await asyncio.wait([send, receive, roamer], return_when=asyncio.FIRST_COMPLETED)
        for q in done:
            if q is send:
                # принимаем команду от клиента и разбиваем ее на аргументы
                send = asyncio.create_task(reader.readline())
                cur_rcv = q.result()
                parsed_cmd = shlex.split(cur_rcv.decode())

                if parsed_cmd[0] == 'quit':
                    break

                # приводим все аргументы к соотв. типу из аннотаций и
                # аргумент - название команды на объект класса Player
                arg_ind = 1
                args_len = len(parsed_cmd)
                cur_cmd = available_cmds[parsed_cmd[0]]
                cur_method = cur_cmd.get_target()
                parsed_cmd[0] = player
                cur_annotations = cur_method.__annotations__

                for i in cur_annotations:
                    if arg_ind == args_len:
                        break
                    if parsed_cmd[arg_ind]:
                        parsed_cmd[arg_ind] = (cur_annotations[i](parsed_cmd[arg_ind]))
                        arg_ind += 1

                # Вызываем нужный метод с сформированным списком аргументов
                # кладем результат в очередь
                res = cur_method.__call__(*parsed_cmd)

                if res[0]:
                    for cur_name in clients:
                        if cur_name != name:
                            await clients[cur_name].put('{} {}'.format(name, res[1][cur_name]))
                        else:
                            await clients[cur_name].put(res[1][cur_name])
                else:
                    await clients[name].put(res[1])

            elif q is receive:
                # достаем результат из очереди и посылаем его клиенту
                receive = asyncio.create_task(clients[name].get())
                cur_rcv = q.result()
##                print(cur_rcv)
                writer.write(cur_rcv.encode())
                await writer.drain()

        else:
            continue
        break

    # закрываем соединение
    send.cancel()
    receive.cancel()

    writer.write("quit".encode())
    await writer.drain()

    del clients[name]
    player.die()
    writer.close()
    await writer.wait_closed()

    await clients[cur_name].put(("{} has disconnected").format(name))

    return True


async def main(game_name, real_password, package_path, players_count):
    """Запуск сервера."""
    global password
    password = real_password
    print("STARING SERVER")
    server = await asyncio.start_server(SIG, '0.0.0.0', 1338)
    print("SERVER STARTED")
    async with server:
        await server.serve_forever()
##    print("GOOD BYE")

def server_starter(game_name, real_password, package_path, players_count):
    asyncio.run(main(game_name, real_password, package_path, players_count))