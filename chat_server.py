"""
Created on Tue Jul 22 00:47:05 2014

@author: alina, zzhang
"""

import time
import socket
import select
import sys
import string
import indexer
import json
import pickle as pkl
from chat_utils import *
import chat_group as grp
import operator


class Server:
    def __init__(self):
        self.new_clients = []  # list of new sockets of which the user id is not known
        self.logged_name2sock = {}  # dictionary mapping username to socket
        self.logged_sock2name = {}  # dict mapping socket to user name
        self.all_sockets = []
        self.group = grp.Group()
        # start server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        # initialize past chat indices
        self.indices = {}
        # sonnet
        # self.sonnet_f = open('AllSonnets.txt.idx', 'rb')
        # self.sonnet = pkl.load(self.sonnet_f)
        # self.sonnet_f.close()
        self.sonnet = indexer.PIndex("AllSonnets.txt")
        #scoreboard for space invaders
        self.scoreboard = {}

    def new_client(self, sock):
        # add to all sockets and to new clients
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
        # read the msg that should have login code plus username
        try:
            msg = json.loads(myrecv(sock))
            print("login:", msg)
            if len(msg) > 0:
                print("------------")
                if msg["action"] == "signup":
                    # print("注册成功")
                    name = msg["name"]
                    pswd = msg["pswd"]
                    self.group.userlist[name] = pswd
                    mysend(sock, json.dumps(
                            {"action": "signup", "status": "success"}))
                    print("注册成功")


                elif msg["action"] == "login":
                    name = msg["name"]
                    pswd = msg["pswd"]
                    print('---',self.group.userlist.items())
                    if self.group.is_member(name) != True: #还没login的状态
                        print("查看是否注册")
                        if name in self.group.userlist.keys(): #user已注册
                            print("查看密码是否正确")
                            if self.group.matched(name, pswd) == True: #密码正确,proceed
                                self.new_clients.remove(sock)
                                self.logged_name2sock[name] = sock
                                self.logged_sock2name[sock] = name
                                if name not in self.indices.keys(): 
                                # load chat history of that user
                                    print("load chat history")
                                    try:
                                        self.indices[name] = pkl.load(
                                            open(name+'.idx', 'rb'))
                                    except IOError:  # chat index does not exist, then create one
                                        self.indices[name] = indexer.Index(name)
                                print(name + ' logged in')
                                self.group.join(name)
                                mysend(sock, json.dumps(
                                    {"action": "login", "status": "ok"}))
                                print("登录成功")
                            elif self.group.matched(name, pswd) != True: #密码错误，报错
                                mysend(sock, json.dumps(
                                    {"action": "login", "status": "wrongpswd"}))
                                print("密码错误，报错")
                            else:
                                print("else")
                        elif name not in self.group.userlist.keys(): #user未注册
                            print("未注册")
                            mysend(sock, json.dumps(
                                    {"action": "login", "status": "needsignup"}))
                        else:            
                            print("else else")
                    else:  # a client under this name has already [logged in]
                        mysend(sock, json.dumps(
                            {"action": "login", "status": "duplicate"}))
                        print(name + ' duplicate login attempt')
                else:
                    print('wrong code received')
                print("Should be print out")
            else:  # client died unexpectedly
                self.logout(sock)
        except:
            self.all_sockets.remove(sock)

    def logout(self, sock):
        # remove sock from all lists
        name = self.logged_sock2name[sock]
        pkl.dump(self.indices[name], open(name + '.idx', 'wb'))
        del self.indices[name] # log out!
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        self.all_sockets.remove(sock)
        self.group.leave(name)
        sock.close()

# ==============================================================================
# main command switchboard
# ==============================================================================
    def handle_msg(self, from_sock):
        # read msg code
        msg = myrecv(from_sock)
        if len(msg) > 0:
            # ==============================================================================
            # handle connect request
            # ==============================================================================
            msg = json.loads(msg)
            if msg["action"] == "connect":
                to_name = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name:
                    msg = json.dumps({"action": "connect", "status": "self"})
                # connect to the peer
                elif self.group.is_member(to_name):
                    to_sock = self.logged_name2sock[to_name]
                    self.group.connect(from_name, to_name)
                    the_guys = self.group.list_me(from_name)
                    msg = json.dumps(
                        {"action": "connect", "status": "success"})
                    for g in the_guys[1:]:
                        to_sock = self.logged_name2sock[g]
                        mysend(to_sock, json.dumps(
                            {"action": "connect", "status": "request", "from": from_name}))
                else:
                    msg = json.dumps(
                        {"action": "connect", "status": "no-user"})
                mysend(from_sock, msg)
# ==============================================================================
# handle messeage exchange: one peer for now. will need multicast later
# ==============================================================================
            elif msg["action"] == "exchange":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                #said = msg["from"]+msg["message"]
                said2 = text_proc(msg["message"], from_name)
                self.indices[from_name].add_msg_and_index(said2)
                for g in the_guys[1:]:
                    to_sock = self.logged_name2sock[g]
                    self.indices[g].add_msg_and_index(said2)
                    mysend(to_sock, json.dumps(
                        {"action": "exchange", "from": msg["from"], "message": msg["message"]}))
# ==============================================================================
#                 listing available peers
# ==============================================================================
            elif msg["action"] == "list":
                from_name = self.logged_sock2name[from_sock]
                msg = self.group.list_all()
                print('msg',msg)
                mysend(from_sock, json.dumps(
                    {"action": "list", "results": '1'}))

            elif msg["action"] == "options":
                from_name = self.logged_sock2name[from_sock]
                ppl_list = self.indices.keys() #在线人员
                print(ppl_list)
                mysend(from_sock, json.dumps(
                    {"action": "options", "results": ppl_list}))
# ==============================================================================
#             retrieve a sonnet
# ==============================================================================
            elif msg["action"] == "poem":
                poem_indx = int(msg["target"])
                from_name = self.logged_sock2name[from_sock]
                print(from_name + ' asks for ', poem_indx)
                poem = self.sonnet.get_poem(poem_indx)
                poem = '\n'.join(poem).strip()
                print('here:\n', poem)
                mysend(from_sock, json.dumps(
                    {"action": "poem", "results": poem}))
# ==============================================================================
#                 time
# ==============================================================================
            elif msg["action"] == "time":
                ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
                mysend(from_sock, json.dumps(
                    {"action": "time", "results": ctime}))
# ==============================================================================
#                 search
# ==============================================================================
            elif msg["action"] == "search":
                term = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                print('search for ' + from_name + ' for ' + term)
                # search_rslt = (self.indices[from_name].search(term))
                search_rslt = '\n'.join(
                    [x[-1] for x in self.indices[from_name].search(term)])
                print('server side search: ' + search_rslt)
                mysend(from_sock, json.dumps(
                    {"action": "search", "results": search_rslt}))
# ==============================================================================
#                 new function: scoreboard
# ==============================================================================
            elif msg["action"] == "submit":
                from_name = self.logged_sock2name[from_sock]
                print("new game score submitted.")
                with open('scoreboard.json', 'r+') as f:
                    scoreboard = json.load(f)
                    score = msg['score']
                    score_old = scoreboard.get(from_name, 0)
                    new_record = "\n"
                    if float(score) > float(score_old):
                        scoreboard[from_name] = float(score)
                        new_record = "\nNew record!"
                    scoreboard_updated = {}
                    sorter = sorted(scoreboard.items(), key=operator.itemgetter(1), reverse=True)
                    for x in sorter:
                        scoreboard_updated[x[0]] = x[1]
                    f.seek(0)
                    json.dump(scoreboard_updated, f)
                    f.truncate()
                    mysend(from_sock, json.dumps(
                    {"action": "feedback", "results": new_record}))
# ==============================================================================
#                 new function: ranking inquiry
# ==============================================================================
            elif msg["action"] == "ranking":
                print("loading scoreboard:")
                with open('scoreboard.json', 'r') as f:
                    scoreboard = json.load(f)
                    board = ""
                    board += "---------------------------\n\
                             Global Space Invader Scoreboard:\n"
                    boardlist = [(x, scoreboard[x]) for x in scoreboard.keys()]
                    board += '\n'.join([f"{i+1}. {boardlist[i][0]}\
                             {boardlist[i][1]} points" for i in range(len(boardlist))])
                    board += "\n---------------------------\n"
                    mysend(from_sock, json.dumps(
                    {"action": "ranking", "results": board}))
# ==============================================================================
#                 new function: ranking inquiry (individual)
# ==============================================================================
            elif msg["action"] == "inquiry":
                with open('scoreboard.json', 'r') as f:
                    scoreboard = json.load(f)
                    peer = msg["target"]
                    try:
                        peer_score = scoreboard[peer]
                        result = f"{peer}'s score: {peer_score}"
                    except:
                        result = "Peer not found. Maybe ask them to try the game out?"
                    mysend(from_sock, json.dumps(
                        {"action": "inquiry", "results":result}
                    ))
# ==============================================================================
# the "from" guy has had enough (talking to "to")!
# ==============================================================================
            elif msg["action"] == "disconnect":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                the_guys.remove(from_name)
                if len(the_guys) == 1:  # only one left
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, json.dumps({"action": "disconnect"}))
# ==============================================================================
#                 the "from" guy really, really has had enough
# ==============================================================================

        else:
            # client died unexpectedly
            self.logout(from_sock)

# ==============================================================================
# main loop, loops *forever*
# ==============================================================================
    def run(self):
        print('starting server...')
        while(1):
            read, write, error = select.select(self.all_sockets, [], [])
            print('checking logged clients..')
            for logc in list(self.logged_name2sock.values()):
                if logc in read:
                    self.handle_msg(logc)
            print('checking new clients..')
            for newc in self.new_clients[:]:
                if newc in read:
                    self.login(newc)
            print('checking for new connections..')
            if self.server in read:
                # new client request
                sock, address = self.server.accept()
                self.new_client(sock)


def main():
    server = Server()
    server.run()


if __name__ == "__main__":
    main()
