# -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 11:22:35 2017

@author: koeniga
"""

import socket

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    server_address = ("192.168.0.10", 10000)
    print("Connecting to %s port %s" % server_address)
    sock.connect(server_address)
    
    
    message = b'Can I join the game?'
    sock.sendall(message)
    answer = sock.recv(1024)
    #if answer == b'':
    #    break
    print(answer.decode('ascii'))
#    top = tkinter.Tk()
    #print("Waiting on another player to join")
    while 1:
        answer = sock.recv(1024)
        if answer.decode('ascii').startswith("Bet"):
            sendBack = input(answer.decode('ascii'))
            sock.sendall(sendBack.encode('ascii'))
            text = sock.recv(1024)
            print(text.decode('ascii'))
            if sendBack.upper().startswith('B'): #bet option
                secondBetPrompt = sock.recv(1024)
                sendBack = input(secondBetPrompt.decode('ascii'))
                sock.sendall(sendBack.encode('ascii'))
            answer = ''.encode('ascii')
        if answer.decode('ascii').startswith("Call"): 
            sendBack = input(answer.decode('ascii'))
            sock.sendall(sendBack.encode('ascii'))
            text = sock.recv(1024)
            print(text.decode('ascii'))
            if sendBack.upper().startswith('R'): #raise option
                secondBetPrompt = sock.recv(1024)
                sendBack = input(secondBetPrompt.decode('ascii'))
                sock.sendall(sendBack.encode('ascii'))
            answer = ''.encode('ascii')
        if answer.decode('ascii').startswith("Exit"):
            break
        else:
#            message = tkinter.StringVar()
#            label = tkinter.Message(top, textvariable=message, relief=tkinter.RAISED)
#            message.set(answer.decode('ascii'))
#            label.pack()
#            top.mainloop()
            print(answer.decode('ascii'))
            answer = ''.encode('ascii')
    
    sock.close()

if __name__ == "__main__":
    main()

    