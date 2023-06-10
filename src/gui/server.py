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
pack_string = ''


async def SIG(reader, writer):
    """Функция, реализуящая функциональности сервера.

    Организует запуск на выполнение принимаемых от пользователя команд,
    а также посылает ответы пользователю или широковещательные сообщения.
    """
    print("HERE WE GO")
    global clients, master, password
    to_login = asyncio.create_task(reader.readline())
    res = await to_login
    to_pass = asyncio.create_task(reader.readline())
    res.decode()[:-1]
    name = res.decode()[:-1]
    print(f"{name} connected")

    if len(clients) == 0:
        master = name

    if name in clients:
        writer.write(("sorry").encode())
        await writer.drain()
        return False
    else:
        writer.write(("hello").encode())
        await writer.drain()

    res = await to_pass
    got_password = res.decode()[:-1]
    print(f"{got_password} received")
    if got_password == password:
        writer.write(("hello").encode())
        await writer.drain()
        ##for cur_name in clients:
        ##    await clients[cur_name].put(("{} has connected").format(name))
    else:
        writer.write(("sorry").encode())
        await writer.drain()
        return False
                
    clients[name] = asyncio.Queue()
##    print(name, 'connected')

    # создаем два задания: на чтение и на запись
    print("OH YESSS")
    send = asyncio.create_task(reader.readline())
    receive = asyncio.create_task(clients[name].get())

    while not reader.at_eof():
        # обрабатываем выполненные задания с учетом того, что они могут закончиться одновременно
        done, pending = await asyncio.wait([send, receive], return_when=asyncio.FIRST_COMPLETED)
        for q in done:
            if q is send:
                # принимаем команду от клиента и разбиваем ее на аргументы
                send = asyncio.create_task(reader.readline())
                cur_rcv = q.result().decode()
                parsed_cmd = shlex.split(cur_rcv)
                for_master = False

                match parsed_cmd[0]:
                    case 'quit':
                        break
                    case 'result':
                        for_master = True
                
                if for_master:
                    await clients[master].put(cur_rcv)

                else:
                    for cur_name in clients:
                        await clients[cur_name].put(cur_rcv)


            elif q is receive:
                # достаем результат из очереди и посылаем его клиенту
                receive = asyncio.create_task(clients[name].get())
                cur_rcv = q.result()
                print(f"SERVER HAS RECEIVED {cur_rcv}")
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
    writer.close()
    await writer.wait_closed()

    await clients[cur_name].put(("{} has disconnected").format(name))

    return True


async def main(game_name, real_password, package_path, players_count):
    """Запуск сервера."""
    global password
    password = real_password
    print("STARING SERVER")
    server = await asyncio.start_server(SIG, '0.0.0.0', 1332)
    print("SERVER STARTED")
    async with server:
        await server.serve_forever()
##    print("GOOD BYE")

def server_starter(game_name, real_password, package_path, players_count):
    asyncio.run(main(game_name, real_password, package_path, players_count))