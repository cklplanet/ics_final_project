#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 13:36:58 2021

@author: bing
"""

# import all the required  modules
import threading
import select
from tkinter import *
from tkinter import font
from tkinter import ttk
from tkinter import messagebox
from chat_utils import *
import json
import time
from datetime import datetime


# GUI class for the chat


class GUI:
    # constructor method
    def __init__(self, send, recv, sm, s):
        # chat window which is currently hidden
        self.Window = Tk()
        self.Window.withdraw()
        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s
        self.my_msg = ""
        self.system_msg = ""
        self.options = []

    def login(self):
        # login window
        self.login = Toplevel()
        # set the title
        self.login.title("Login")
        self.login.resizable(width=False,
                             height=False)
        self.login.configure(width=400,
                             height=300)
        # guide
        self.pls = Label(self.login,
                         text="Please login to continue",
                         justify=CENTER,
                         font="Helvetica 14 bold")

        self.pls.place(relheight=0.15,
                       relx=0.2,
                       rely=0.07)

        # Name
        self.labelName = Label(self.login,
                               text="Name: ",
                               font="Helvetica 12")

        self.labelName.place(relheight=0.2,
                             relx=0.1,
                             rely=0.2)

        self.entryName = Entry(self.login,
                               font="Helvetica 14")

        self.entryName.place(relwidth=0.4,
                             relheight=0.12,
                             relx=0.35,
                             rely=0.2)

        # Password
        self.labelPswd = Label(self.login,
                               text="Password: ",
                               font="Helvetica 12")

        self.labelPswd.place(relheight=0.2,
                             relx=0.1,
                             rely=0.4)

        self.entryPswd = Entry(self.login,
                               font="Helvetica 14")

        self.entryPswd.place(relwidth=0.4,
                             relheight=0.12,
                             relx=0.35,
                             rely=0.4)

        # set the focus of the curser
        self.entryName.focus()

        # create a Continue Button
        # along with action
        self.go = Button(self.login,
                         text="CONTINUE",
                         font="Helvetica 14 bold",
                         command=lambda: self.goAhead(self.entryName.get(), self.entryPswd.get()))

        self.go.place(relx=0.4,
                      rely=0.55)

        # sign up button
        self.signup = Button(self.login,
                         text="SIGN UP",
                         font="Helvetica 14 bold",
                         command=lambda: self.signUp(self.entryName.get(), self.entryPswd.get()))

        self.signup.place(relx=0.7,
                      rely=0.55)
        
        self.Window.mainloop()


    def signUp(self, name, pswd):
        self.signup = Toplevel()
        self.signup.title("Sign up")
        self.signup.resizable(width=False,
                             height=False)
        self.signup.configure(width=400,
                             height=300)

        # guide
        self.guide = Label(self.signup,
                         text="Create a new account!",
                         justify=CENTER,
                         font="Helvetica 14 bold")

        self.guide.place(relheight=0.15,
                       relx=0.2,
                       rely=0.07)

        # Name
        self.labelName = Label(self.signup,
                               text="Name: ",
                               font="Helvetica 12")

        self.labelName.place(relheight=0.2,
                             relx=0.1,
                             rely=0.2)

        self.entryName = Entry(self.signup,
                               font="Helvetica 14")
        self.entryName.insert(0,name)

        self.entryName.place(relwidth=0.4,
                             relheight=0.12,
                             relx=0.35,
                             rely=0.2)

        # Password
        self.labelPswd = Label(self.signup,
                               text="New password: ",
                               font="Helvetica 12")

        self.labelPswd.place(relheight=0.2,
                             relx=0.1,
                             rely=0.4)

        self.entryPswd = Entry(self.signup,
                               font="Helvetica 14")
        self.entryPswd.insert(0,pswd)

        self.entryPswd.place(relwidth=0.4,
                             relheight=0.12,
                             relx=0.35,
                             rely=0.4)

        self.proceed = Button(self.signup,
                         text="CREATE AND LOG IN",
                         font="Helvetica 14 bold",
                         command=lambda: self.createNewUser(self.entryName.get(), self.entryPswd.get()))

        self.proceed.place(relx=0.4,
                      rely=0.55)

        self.Window.mainloop() #?


    def createNewUser(self, name, pswd):
        if len(name) > 0 and len(pswd) > 0:
            msg = json.dumps({"action": "signup", "name": name, "pswd": pswd})
            self.send(msg)
            response = json.loads(self.recv())
            if response["status"] == 'success':
                print("真的成功创建了") # 还未登录
                # 登录！
                self.goAhead(name, pswd) # 大爷请这边走！
            else:
                print("???")
            



    def goAhead(self, name, pswd):
        if len(name) > 0 and len(pswd) > 0:
            msg = json.dumps({"action": "login", "name": name, "pswd": pswd})
            # msg = json.dumps({"action": "signup", "name": name, "pswd": pswd})
            self.send(msg)
            print(206, msg)
            response = json.loads(self.recv())
            print(207, response)
            if response["status"] == 'ok':
                self.login.destroy()
                self.sm.set_state(S_LOGGEDIN)
                self.sm.set_myname(name)
                self.layout(name) 
                self.textCons.config(state=NORMAL)
                self.textCons.insert(END, menu + "\n\n")
                self.textCons.config(state=DISABLED)
                self.textCons.see(END)
                #  the thread to receive messagesF
                process = threading.Thread(target=self.proc)
                process.daemon = True
                process.start()
            elif response["status"] == 'wrongpswd':
                messagebox.showerror(title='warning', message='Wrong password!')
            elif response["status"] == 'needsignup':
                messagebox.showinfo(title='notice', message='Please sign up first')
            
            print(221)

        ##  the thread to receive messages
        # process = threading.Thread(target=self.proc)
        # process.daemon = True
        # process.start()
        print(227)

    # The main layout of the chat
    def layout(self, name):

        self.name = name
        # to show chat window
        self.Window.deiconify()
        self.Window.title("CHATROOM")
        self.Window.resizable(width=False,
                              height=False)
        self.Window.configure(width=470,
                              height=550,
                              bg="#17202A")
                            

        self.labelHead = Label(self.Window,
                               bg="#17202A",
                               fg="#EAECEE",
                               text=self.name,
                               font="Helvetica 13 bold",
                               pady=5)

        self.labelHead.place(relwidth=1,
                             rely=0.04,
                             relheight=0.06)

        self.line = Label(self.Window,
                          width=450,
                          bg="#ABB2B9")

        self.line.place(relwidth=1,
                        rely=0.1,
                        relheight=0.012)

        self.textCons = Text(self.Window,
                             width=20,
                             height=2,
                             bg="#17202A",
                             fg="#EAECEE",
                             font="Helvetica 14",
                             padx=5,
                             pady=5)

        self.textCons.place(relheight=0.745,
                            relwidth=1,
                            rely=0.1)

        self.labelBottom = Label(self.Window,
                                 bg="#ABB2B9",
                                 height=80)

        self.labelBottom.place(relwidth=1,
                               rely=0.825)

        self.entryMsg = Entry(self.labelBottom,
                              bg="#2C3E50",
                              fg="#EAECEE",
                              font="Helvetica 13")

        # place the given widget
        # into the gui window
        self.entryMsg.place(relwidth=0.74,
                            relheight=0.06,
                            rely=0.008,
                            relx=0.011)

        self.entryMsg.focus()

        # create a Send Button
        self.buttonMsg = Button(self.labelBottom,
                                text="Send",
                                font="Helvetica 10 bold",
                                width=20,
                                bg="#ABB2B9",
                                command=lambda: self.sendButton(self.entryMsg.get()))

        self.buttonMsg.place(relx=0.77,
                             rely=0.04,
                             relheight=0.025,
                             relwidth=0.22)

        self.textCons.config(cursor="arrow")

        # create a drop down box
        # def update_options():
        #     self.my_msg = 'who'
        #     print(316)
        #     self.options.after(1000, update_options)
        #     self.login.update()
        
        def update_options(event): # self
            print(321)
            msg = json.dumps({"action": "list"})
            print(322)
            self.send(msg)
            print(324, msg)
            response = json.loads(self.recv())
            print(326, response)
            if response["action"] == 'list':
                print("yes")
            ### 传出去了没收到
            # pswd = 123
            # msg = json.dumps({"action": "login", "name": name, "pswd": pswd})
            # # msg = json.dumps({"action": "signup", "name": name, "pswd": pswd})
            # self.send(msg)
            # print(206, msg)
            # response = json.loads(self.recv())
            # print(207, response)
                
            
        options = ['a','b']



        def selected(event): # 路径: self.my_msg
            self.my_msg = 'c' + clicked.get()
            # print(self.my_msg)
            # ppl = response['results'].split('\n')[1]
            

        clicked = StringVar()
        clicked.set("Online users")
        self.drop = OptionMenu(self.labelBottom, clicked, *options, command=update_options)
        self.drop.place(relx=0.77,
                             rely=0.008,
                             relheight=0.025,
                             relwidth=0.22)

        # create a scroll bar
        scrollbar = Scrollbar(self.textCons)

        # place the scroll bar
        # into the gui window
        scrollbar.place(relheight=1,
                        relx=0.974)

        scrollbar.config(command=self.textCons.yview)

        self.textCons.config(state=DISABLED)
        
        
        
        
        def update_clock():
            raw = datetime.now()
            time_now = raw.strftime('%H:%M:%S')
            # print(time_now)
            # time_display.setvar(str(time_now))
            time_display = Label(self.Window,
                    text=time_now,
                    bg="#17202A",
                    fg="#EAECEE",
                    font="Helvetica 13 bold",
                    pady=5)
            time_display.place(relwidth=1)
            
            time_display.after(1000, update_clock)
            self.login.update()


        # self.Window.update() #!!!!!!
        # self.Window.mainloop()
        update_clock()
        print(376)


    # function to basically start the thread for sending messages

    def sendButton(self, msg):
        # self.textCons.config(state=DISABLED)
        self.my_msg = msg    # input <<----------------------------------------------
        # print(msg)
        self.entryMsg.delete(0, END)
        self.textCons.config(state=NORMAL)
        self.textCons.insert(END, msg.strip() + "\n")
        self.textCons.config(state=DISABLED)
        self.textCons.see(END)

    def proc(self): 
        # print(self.msg)
        while True:
            read, write, error = select.select([self.socket], [], [], 0)
            peer_msg = []
            # print(self.msg)
            if self.socket in read:
                peer_msg = self.recv()
            if len(self.my_msg) > 0 or len(peer_msg) > 0:
                print(397)
                # print('sys---',self.system_msg)
                self.system_msg = self.sm.proc(self.my_msg, peer_msg) #************************
                # print('sys---',self.system_msg)
                # self.options = 
                # print("options", self.options)
                self.my_msg = ""
                self.textCons.config(state=NORMAL)
                self.textCons.insert(END, self.system_msg + "\n\n")
                self.textCons.config(state=DISABLED)
                self.textCons.see(END)

    def run(self):
        self.login()


# create a GUI class object
if __name__ == "__main__":
    #g = GUI()
    pass
