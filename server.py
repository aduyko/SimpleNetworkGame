from socket import *
import select
import random

# Player class keeps track of player name, status, and socket.
class Player:
  socket = ''
  name = ''
  status = 'Busy'
  def __init__(self,iSock):
    self.socket = iSock
  #Used for ensuring a message gets delivered completely before delivering another.
  #I used getOk, sendText, and sendCommand to avoid issues with stream
  #and to deal in discrete messages.
  def getOk(self):
    message = self.socket.recv(1024)
    if message == 'ok':
      pass
    else:
      raise Exception("Problem with message")
  def sendText(self,contents):
    self.socket.send('text||' + str(contents))
    self.getOk()
  def sendCommand(self,command):
    self.socket.send(command)
    self.getOk()
  #checks if player with given socket is in list.
  def find(self,sock):
    if self.socket==sock:
      return True
    else:
      return False
#Game class keeps track of the stack and stack manipulation
class Game():
  stack = []
  #create random stack between 3-5 and 1-7
  def __init__(self):
    stacksize = random.randint(3,5)
    for i in range(0,stacksize):
      self.stack.append(random.randint(1,7))
  def __str__(self):
    return " ".join((map(str, self.stack)))
  def remove(self, pid, num):
    self.stack[pid-1]=self.stack[pid-1]-num
  #checck if game over
  def over(self):
    for i in self.stack:
      if i>0:
        return False
    return True
#init server socket
serverSock = socket(AF_INET, SOCK_STREAM)
host = ''
port = 5247
#sockets list used for select
sockets = [serverSock]
#players list used for making games
allplayers = []
players = []
#game states
turn = 1
game = False
global myGame
#launch server socket
serverSock.bind((host, port))
serverSock.listen(2)
print("Server started on port: " + str(port))

#server logic
while True:
  inputsel, outputsel, exceptsel = select.select(sockets,[],[])
  #doStuff is used for Game move order which is after this
  doStuff = False

  #for received messages
  for s in inputsel:
    #add new sockets
    if s==serverSock:
      clientSock, addr = serverSock.accept()
      print 'Got connection from', addr
      #append our socket to our list to listen for it
      sockets.append(clientSock)
      #add the player and prompt him
      allplayers.append(Player(clientSock))
      allplayers[-1].sendText('Thank you for connecting. Please login to play, or type "help" for more options.')
      allplayers[-1].sendCommand('prompt')
    else:
      #find the player based on socket
      curp = ''
      for p in allplayers:
        if p.find(s):
          curp = p
      try:
        #get message from player
        message = s.recv(1024)
        message = message.split(' ')
        #depending on the message, do whatever
        if message[0]=='help':
          #reprompt if it was help, help is done client-side
          curp.sendCommand('prompt')
        elif message[0]=='login':
          #attempt to login, making sure the user is not already logged in
          #and that theri username is unique
          alreadyUsed = False
          for p in allplayers:
            if p.name==message[1]:
              alreadyUsed=True
          if curp.name!='':
            curp.sendText("You are already logged in as " + curp.name)
            curp.sendCommand('prompt')
          elif alreadyUsed==True:
            curp.sendText("Another user is already logged in as " + message[1] + ". Please pick another name.")
            curp.sendCommand('prompt')
          #i am only doing two playres at a time, so you cannot log in
          #if a game is underway
          elif len(players)==2:
            curp.sendText("You cannot queue up for a game while one is ongoing. Please wait.")
            curp.sendCommand('prompt')
          #log a player in
          else:
            curp.name = message[1]
            curp.status = 'Available'
            players.append(curp)
            curp.sendText("Logged in as " + message[1])
            curp.sendCommand('wait')
        elif message[0]=='exit':
          #exit. Also called if the client aborts their program.
          if curp in players:
            players.remove(curp)
            players[0].sendText("The other player has quit.")
            players[0].sendCommand('wait')
            game = False
          allplayers.remove(curp)
          sockets.remove(curp.socket)
          curp.sendText("Game Exited.")
          curp.socket.close()
          break
        elif message[0]=='remove':
          #game logic. Sanity checks, then removal
          message[1] = int(message[1])
          message[2] = int(message[2])
          if message[1]<1 or message[1]>len(myGame.stack):
            curp.sendText("Invalid stack index. Please pick again.")
            curp.sendCommand("prompt")
          elif message[2]<0:
            curp.sendText("You cannot remove a negative number. Please pick again.")
            curp.sendCommand("prompt")
          elif message[2]>myGame.stack[message[1]-1]:
            curp.sendText("You cannot remove more stones than exist in that stack. Please pick again.")
            curp.sendCommand("prompt")
          else:
            #tell both players what happened
            myGame.remove(message[1],message[2])
            colstring = str(curp.name)+" removes "+str(message[2])+" stones from column " + str(message[1])
            players[0].sendText(colstring)
            players[1].sendText(colstring)
            #next turn
            turn*=-1
            #dont do stuff if no move was made or an error hapepned.
            doStuff=True
        else:
          #otherwise something weirdh appened so prompt again
          curp.sendCommand('prompt')
      except:
        #if a client aborts, the server logs this
        print 'CONNECTION ABORTED BY!!'+str(s)
        break
  #check if there are enough players for a game
  if game==False:
    if len(players)==2:
      #start a game autoamtically
      game=True
      #make new game
      myGame = Game()
      #get info about the game
      stacksize = len(myGame.stack)
      stackstr = "Set "
      for i in range(1,stacksize+1):
        stackstr += str(i) + " "
      curstack = "Size " + str(myGame)
      #print info about the game to users
      players[0].sendText("Game Started between " + players[0].name + " and " + players[1].name)
      players[0].sendText(stackstr)
      players[0].sendText(curstack)
      players[1].sendText("Game Started between " + players[0].name + " and " + players[1].name)
      players[1].sendText(stackstr)
      players[1].sendText(curstack)

      #tell users whats going on
      players[0].sendText("Make a move!")
      players[0].sendCommand('prompt')
      players[1].sendText("Opponents turn first.")

  #if a game is underway, and the user made a move:
  elif game==True and doStuff==True:
      #print game info
      stacksize = len(myGame.stack)
      stackstr = "Set "
      for i in range(1,stacksize+1):
        stackstr += str(i) + " "
      curstack = "Size " + str(myGame)
      players[0].sendText(stackstr)
      players[0].sendText(curstack)
      players[1].sendText(stackstr)
      players[1].sendText(curstack)

      #check if the game is over!
      if myGame.over():
        turn*=-1
        if turn==-1:
          players[1].sendText("You win!")
          players[0].sendText(players[1].name + " wins!")
        else:
          players[0].sendText("You win!")
          players[1].sendText(players[0].name + " wins!")
        #log players out after a game
        for p in players:
          p.name=''
          p.status='Busy'
          p.sendText("You have been logged out. Log in again to start a new game.")
          p.sendCommand("prompt")
        players=[]
        game = False
      #continue the game if its not over/
      else:
        if turn==-1:
          players[1].sendText("Now you make a move!")
          players[1].sendCommand('prompt')
          players[0].sendText("Opponents turn.")
        else:
          players[0].sendText("Now you make a move!")
          players[0].sendCommand('prompt')
          players[1].sendText("Opponents turn.")