from socket import *
import sys
#host info is args
argv = sys.argv   
host = argv[1]
port = int(argv[2])

#command stuff
chunks = []
command = ''

#functions for streamlniing info from server
def numChunks():
  global chunks
  return len(chunks)
def getMessage(s):
  global chunks
  global command
  message = s.recv(1024)
  chunks = message.split('||')
  command = chunks[0]
  s.send('ok')

#client side sanity checks for command
def checkCommand(str):
  if str[0]=='help' and len(str)==1:
    return True
  elif str[0]=='login' and len(str)==2:
    return True
  elif str[0]=='remove' and len(str)==3:
    if str[1].isdigit() and str[2].isdigit():
      return True
    else:
      return False
  elif str[0]=='exit' and len(str)==1:
    return True
  else:
    return False
#method to print help
def printHelp():
  print("Commands:")
  print("help : Returns a list of commands")
  print("login x : attempts to log you into the server with the name 'x'")
  print("remove x y : removes x stones from set y")
  print("exit : exits from the game")

#launch socket
s = socket(AF_INET, SOCK_STREAM)

print ("Connecting to port:" + str(port))
s.connect((host, port))
playing = True
while playing:
  #Connection accepted
  try:
    #get message
    getMessage(s)
    #figure out waht to do
    if command=='wait':
      #if wait, wait
      print("Please wait for an opponent.")
    elif command=='text':
      #print text
      print(chunks[1])
    elif command=='prompt':
      #get prompt
      myIn = raw_input("Input:")
      check = myIn.split(' ')
      send = checkCommand(check)
      while send==False:
        print("Error in input. Type 'help' for help.")
        myIn = raw_input("Input:")
        check = myIn.split(' ')
        send = checkCommand(check)
      if check[0]=='help':
        printHelp()
      #always send input for prompt if it is valid
      s.send(myIn)
  except:
    #if the user aborts, send an exit prompt and break
    s.send('exit')
    print("Game closed.")
    playing=False
    break