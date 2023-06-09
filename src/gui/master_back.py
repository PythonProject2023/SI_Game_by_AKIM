import time
import socket
import multiprocessing
from parser import parse_package


semop_window = multiprocessing.Semaphore(value=0)
game_params = None


class Player:

    def choose_button(cls, th, q):
        request = f"choose {th} {q}".encode()
        cls.sock.send(request)
    
    def answer_button(self):
        request = "answer"
        self.sock.send(request)

    def result_button(self):
        ## вместо result должен быть текст из текстового поля с ответом пользователя
        request = "result RESULT"
        self.sock.send(request)

    def my_read(self, sock):
        """Функция, читающая из сокета."""
        time.sleep(0.1)
        while True:
            res = sock.recv(4096)
            res = res.decode().split()
            match res[0]:
                case "choose":
                    print("CHOOSE", res)
                case "answer":
                    print("ANSWER", res)
                case "right":
                    print("RIGHT", res)
        return True

    def play(self, game_name, players_count):
        pass


    def __init__(self, game_name, password, package_path, players_count, child_conn):
        self.name = 'master_oogway'
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('localhost', 1340))
        self.sock.send((f"{self.name}\n").encode())
        self.res = self.sock.recv(4096)

        if self.res == b'hello':
            self.sock.send(password.encode())
            self.res = self.sock.recv(4096)
            reader = multiprocessing.Process(target=self.my_read, args=(self.sock,))
            writer = multiprocessing.Process(target=self.my_write, args=(self.sock,))

            reader.start()
            writer.start()
        else:
            print(f"Nickname {self.name} is allready taken, please log in with another nickname")
            self.sock.close()
        self.play(game_name, package_path, players_count)

def master_starter(game_name, password, package_path, players_count, child_conn):
    Player(game_name, password, package_path, players_count, child_conn)

##master_starter('game_name', 'password', 'Game.siq', 3)