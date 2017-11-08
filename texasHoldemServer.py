# -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 11:12:58 2017

@author: koeniga
"""

import socket
import numpy
import time

deckOfCards = [
"AH", "2H", "3H", "4H", "5H", "6H", "7H",
"8H", "9H", "TH", "JH", "QH", "KH",
"AD", "2D", "3D", "4D", "5D", "6D", "7D",
"8D", "9D", "TD", "JD", "QD", "KD",
"AS", "2S", "3S", "4S", "5S", "6S", "7S",
"8S", "9S", "TS", "JS", "QS", "KS",
"AC", "2C", "3C", "4C", "5C", "6C", "7C",
"8C", "9C", "TC", "JC", "QC", "KC"
]

playerList = []
clients = []
addresses = []

class Player:
    def __init__(self, number):
        self.number = number
        self.cardOne = 0
        self.cardTwo = 0
        self.handStrength = 0
        self.handType = ""
        self.hand = []
        self.chips = 5000
        self.betThisTurn = 0
        self.folded = False
        
def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    server_address = ('192.168.0.10', 10000)
    print ('starting up on %s port %s' %server_address)
    sock.bind(server_address)
    expectedPlayers = 2
    sock.listen(expectedPlayers)
    numberOfPlayers = 0
    while True:
        connection, client_address = sock.accept()
        clients.append(connection)
        addresses.append(client_address)
        
        print("connection from", client_address)
            
        msg = connection.recv(1024)
        if msg == b'':
            raise RuntimeError("Connection Broken")
        
        if msg == b'Can I join the game?':
            print("received", msg.decode('ascii'))
            if msg == "quit":
                connection.close()
            numberOfPlayers += 1
            response = b"Welcome to the Game Player " + str(numberOfPlayers).encode()
            connection.sendall(response)
            if numberOfPlayers >= expectedPlayers:
                for x in clients:
                    x.sendall(b'Beginning the Game Now')
                beginGame(numberOfPlayers)
            #connection.close()
        else:
            print("No more Data from", client_address)
            break

def beginGame(numberOfPlayers):
    global playerList
    gameOn = True
    for i in range(numberOfPlayers):
            playerList.append(Player(i+1))
    while gameOn:
        currentHand = list(deckOfCards)
        for i in playerList:
            cardOne = numpy.random.choice(currentHand, 1)
            currentHand.remove(cardOne)
            cardTwo = numpy.random.choice(currentHand, 1)
            currentHand.remove(cardTwo)
            i.cardOne = cardOne[0]
            i.cardTwo = cardTwo[0]
            print("Player", i.number, "Hand:", i.cardOne, i.cardTwo)
            clients[i.number-1].sendall("\nYour Hand: {:s} {:s}".format(i.cardOne, i.cardTwo).encode())
        
        time.sleep(0.1)
        handOver = False
        pot = 0
        pot = anteUp(pot)
        pot, handOver = bettingPhase(pot)
        
        community = []
        #the flop
        currentHand = burnCard(currentHand)
        currentHand, community = flop(currentHand)
        print("Community After Flop:", community)
        if handOver == False:
            for i in playerList:
                clients[i.number-1].sendall("\nYour Hand: {:s} {:s}".format(i.cardOne, i.cardTwo).encode())
                time.sleep(0.1)
                clients[i.number-1].sendall("Community After Flop: {0}, {1}, {2}\n".format(*community).encode('ascii'))
        pot, handOver = bettingPhase(pot)    
        
        #the turn
        currentHand = burnCard(currentHand)
        currentHand, community = turn(currentHand, community)
        print("Community After Turn:", community)
        if handOver == False:
            for i in playerList:
                clients[i.number-1].sendall("\nYour Hand: {:s} {:s}".format(i.cardOne, i.cardTwo).encode())
                time.sleep(0.1)
                clients[i.number-1].sendall("Community After Turn: {0}, {1}, {2}, {3}\n".format(*community).encode('ascii'))
        pot, handOver = bettingPhase(pot)
        
        #the river
        currentHand = burnCard(currentHand)
        currentHand, community = river(currentHand, community)
        #community = ['AS', 'KS', 'QS', 'JS', 'TS']
        print("Community After River:", community)
        if handOver == False:
            for i in playerList:
                clients[i.number-1].sendall("\nYour Hand: {:s} {:s}".format(i.cardOne, i.cardTwo).encode())
                time.sleep(0.1)
                clients[i.number-1].sendall("Community After River: {0}, {1}, {2}, {3}, {4}\n".format(*community).encode('ascii'))
        pot, handOver = bettingPhase(pot)
        
        if handOver == False:
            winner = playerList[0]
            otherWinners = []
            for i in range(numberOfPlayers):
                if playerList[i].folded == False:
                    sevenCards = []
                    sevenCards.append(playerList[i].cardOne)
                    sevenCards.append(playerList[i].cardTwo)
                    for j in range(len(community)):
                        sevenCards.append(community[j])
                    #print("Seven Card Hand", i+1, sevenCards)
                    
                    sortedCards = sortCards(sevenCards)
                    
                    findBestHand(sortedCards, i)
                    print("Best 5 Cards:", playerList[i].hand)
                    hand = playerList[i].hand
                    #hand.insert(0, i.number)
                    #print(hand)
                    for x in clients:
                        x.sendall("Player {0}'s 5 Card Hand {1}, {2}, {3}, {4}, {5}".format(playerList[i].number, *hand).encode('ascii'))
                        time.sleep(0.1)
                    
                    if playerList[i].handStrength == winner.handStrength:
                        otherWinners.append(playerList[i])
                    if playerList[i].handStrength > winner.handStrength:
                        otherWinners[:] = []
                        winner = playerList[i]
            if len(otherWinners) == 0:
                print("Player {:d} Wins the Hand With a {:s}".format(winner.number, winner.handType))
                winner.chips += pot
                for x in clients:
                    x.sendall("Player {:d} Wins the Hand With a {:s}".format(winner.number, winner.handType).encode('ascii'))
                    time.sleep(0.1)
            else:
                for x in otherWinners:
                    for i in range(5):
                        if cardRank(x.hand[i][0]) > cardRank(winner.hand[i][0]):
                            winner = x
                            break
                        if cardRank(x.hand[i][0]) < cardRank(winner.hand[i][0]):
                            break
                print("Player {:d} Wins the Hand With a {:s}".format(winner.number, winner.handType))
                winner.chips += pot
                for x in clients:
                    x.sendall("Player {:d} Wins the Hand With a {:s}".format(winner.number, winner.handType).encode('ascii'))
            
        else:
            for i in playerList:
                if i.folded == False:
                    print("Player {:d} Wins Because All Other Players Folded".format(i.number))
                    for x in clients:
                        x.sendall("Player {:d} Wins Because All Other Players Folded".format(i.number).encode('ascii'))
                    i.chips += pot

        nextHandPlayers = []
        pot = 0
        #reset hand specific values and remove any players out of chips
        for i in playerList:
            i.hand[:] = []
            i.folded = False
            if i.chips == 0:
                print("Player {:d} is Out of Chips!".format(i.number))
                for x in clients:
                    x.sendall("Player {:d} is Out of Chips!".format(i.number).encode('ascii'))
                    time.sleep(0.1)
                #clients[i.number-1].sendall("Game's Over For You Nerd. Bye.".encode('ascii'))
                #clients[i.number-1].sendall("Exit".encode('ascii'))
            else:
                nextHandPlayers.append(i)
                
        if len(nextHandPlayers) == 1:
            for x in clients:
                x.sendall("Only 1 Player Left! Player {:d} Wins!".format(nextHandPlayers[0].number).encode('ascii'))
                time.sleep(0.1)
                x.sendall("Exit".encode('ascii'))
                time.sleep(0.1)
                x.close()
            x[:] = []
            print("Only 1 Player Left! Player {:d} Wins!".format(nextHandPlayers[0].number))
            gameOn = False
        playerList = nextHandPlayers
        print("\nStandings After Hand:")
        for x in clients:
            x.sendall("\nStandings After Hand:".encode('ascii'))
        displayStandings()
        print("\nNEW HAND!")
        for x in clients:
            x.sendall("\nNEW HAND!".encode('ascii'))
        
def burnCard(ch):
    burnCard = numpy.random.choice(ch, 1)
    ch.remove(burnCard)
    return ch

def flop(ch):
    flop = []
    cardOne = numpy.random.choice(ch, 1)
    flop.append(cardOne[0])
    ch.remove(cardOne)
    cardTwo = numpy.random.choice(ch, 1)
    flop.append(cardTwo[0])
    ch.remove(cardTwo)
    cardThree = numpy.random.choice(ch, 1)
    flop.append(cardThree[0])
    ch.remove(cardThree)
    
    return ch, flop
    
def turn(ch, com):
    card = numpy.random.choice(ch, 1)
    ch.remove(card)
    com.append(card[0])
    return ch, com
    
def river(ch, com):
    card = numpy.random.choice(ch, 1)
    ch.remove(card)
    com.append(card[0])
    return ch, com

def cardRank(val):
    if val == "A":
        return 14
    if val == "K":
        return 13
    if val == "Q":
        return 12
    if val == "J":
        return 11
    if val == "T":
        return 10
    return int(val)
    
def sortCards(sevCards):
    sortedDeck = []
    while sevCards:
        biggest = sevCards[0]
        for x in sevCards:
            if cardRank(x[0]) > cardRank(biggest[0]):
                biggest = x
        sortedDeck.append(biggest)
        sevCards.remove(biggest)
    #print(sortedDeck)
    return sortedDeck
    
def findBestHand(cards, playerNum):
    backup = list(cards)
    maxFreq, maxVal, secondMaxFreq, secondMaxVal = findFrequencies(cards, playerNum)
    #print(maxFreq, maxVal, secondMaxFreq, secondMaxVal)
    straight, typeStraight = hasStraight(backup, playerNum)
    flush, typeFlush = hasFlush(backup, playerNum)
    
    if straight and flush:
        sfType = straightFlush(backup, typeFlush)
        if sfType[:1] == 'A':
            print("Royal Flush! {:s}".format(sfType))
            playerList[playerNum].handStrength = 10
            playerList[playerNum].handType = "Royal Flush! {:s}".format(sfType)
        else:
            print("Straight Flush! {:s}".format(sfType))
            playerList[playerNum].handStrength = 9
            playerList[playerNum].handType = "Straight Flush! {:s}".format(sfType)
    elif maxFreq == 4:
        print("Four {:s}'s".format(maxVal))
        playerList[playerNum].handStrength = 8
        playerList[playerNum].handType = "Four {:s}'s".format(maxVal)
    elif (maxFreq == 3 and (secondMaxFreq == 2 or secondMaxFreq == 3)):
        print("Full House! {:s}'s and {:s}'s!".format(maxVal, secondMaxVal))
        playerList[playerNum].handStrength = 7
        playerList[playerNum].handType = "Full House! {:s}'s and {:s}'s!".format(maxVal, secondMaxVal)
    elif flush:
        print("{:s} Flush!".format(typeFlush))
        playerList[playerNum].handStrength = 6
        playerList[playerNum].handType = "{:s} Flush!".format(typeFlush)
    elif straight:
        print("Straight! {:s}".format(typeStraight))
        playerList[playerNum].handStrength = 5
        playerList[playerNum].handType = "Straight! {:s}".format(typeStraight)
    elif maxFreq == 3 and secondMaxFreq == 1:
        print("Three {:s}'s!".format(maxVal))
        playerList[playerNum].handStrength = 4
        playerList[playerNum].handType = "Three {:s}'s!".format(maxVal)
    elif maxFreq == 2 and secondMaxFreq == 2:
        print("Two Pair! {:s}'s and {:s}'s!".format(maxVal, secondMaxVal) )
        playerList[playerNum].handStrength = 3
        playerList[playerNum].handType = "Two Pair! {:s}'s and {:s}'s!".format(maxVal, secondMaxVal) 
    elif maxFreq == 2 and secondMaxFreq == 1:
        print("Pair of {:s}'s!".format(maxVal))
        playerList[playerNum].handStrength = 2
        playerList[playerNum].handType = "Pair of {:s}'s!".format(maxVal)
    else:
        print("High Card {:s}".format(maxVal))
        playerList[playerNum].handStrength = 1
        playerList[playerNum].handType = "High Card {:s}".format(maxVal)

def findFrequencies(cards, playerNum):
    #get most common cards
    maxFreq = 0
    maxValue = ""
    originalCards = list(cards)
    while cards:
        freq = 0
        value = ""
        for x in cards:
            value = cards[0][0]
            if cardRank(x[0]) == cardRank(value):
                freq+=1
        cards.remove(cards[0])
        if(freq > maxFreq):
            maxFreq = freq
            maxValue = value
    
    #remove the most freqeuent values from the list 
    #and add a possible pair to the players hand
    secondMost = []
    for x in originalCards:
        if(x[0] != maxValue):
            secondMost.append(x)
        elif maxFreq != 1:
            playerList[playerNum].hand.append(x)
    if maxFreq == 1:
        maxValue = ""
    
    #get second most frequent values
    secondMaxFreq = 0
    secondMaxValue = ""
    while secondMost:
        freq = 0
        value = ""
        for x in secondMost:
            value = secondMost[0][0]
            if cardRank(x[0]) == cardRank(value):
                freq+=1
        secondMost.remove(secondMost[0])
        if freq > secondMaxFreq:
            secondMaxFreq = freq
            secondMaxValue = value
    
    #add a second pair to the players hand if need be
    if secondMaxFreq !=1:
        for x in originalCards:
            if(x[0] == secondMaxValue) and len(playerList[playerNum].hand) < 5:
                playerList[playerNum].hand.append(x)
    if secondMaxFreq ==1:
        secondMaxValue = ""
            
    #append the highest remaining cards up to 5 at most
    for x in originalCards:
        if (x[0] != maxValue and x[0] != secondMaxValue) and len(playerList[playerNum].hand) < 5:
            playerList[playerNum].hand.append(x)
    
    return maxFreq, maxValue, secondMaxFreq, secondMaxValue
    
def hasFlush(sevCards, playerNum):
    hearts, diamonds, clubs, spades = (0,)*4
    for i in range(len(sevCards)):  
        if sevCards[i][1] == 'H':
            hearts +=1
            if hearts > 4:
                playerList[playerNum].hand[:] = [] #empty hand
                for val in sevCards:
                    if val[1] == 'H':
                        playerList[playerNum].hand.append(val)
                return True, "Hearts"
        if sevCards[i][1] == 'D':
            diamonds +=1
            if diamonds > 4:
                playerList[playerNum].hand[:] = [] #empty hand
                for val in sevCards:
                    if val[1] == 'D':
                        playerList[playerNum].hand.append(val)
                return True, "Diamonds"
        if sevCards[i][1] == 'C':
            clubs +=1
            if clubs > 4:
                playerList[playerNum].hand[:] = [] #empty hand
                for val in sevCards:
                    if val[1] == 'C':
                        playerList[playerNum].hand.append(val)
                return True, "Clubs"
        if sevCards[i][1] == 'S':
            spades +=1
            if spades > 4:
                playerList[playerNum].hand[:] = [] #empty hand
                for val in sevCards:
                    if val[1] == 'S':
                        playerList[playerNum].hand.append(val)
                return True, "Spades"
    return False, "No Flush"
    
def hasStraight(backup, playerNum):
    straightString = ""
    for i in range(3):
        straightString = ""
        if cardRank(backup[i][0]) - 1 == cardRank(backup[i+1][0]):
            straightString += backup[i][0] + ", "
            straightString += backup[i+1][0] + ", "
            #print("Two In a Row")
            if cardRank(backup[i+1][0]) - 1 == cardRank(backup[i+2][0]):
                straightString += backup[i+2][0] + ", "
                #print("Three In a Row")
                if cardRank(backup[i+2][0]) - 1 == cardRank(backup[i+3][0]):
                    straightString += backup[i+3][0] + ", "
                    #print("Four In a Row")
                    if cardRank(backup[i+3][0]) - 1 == cardRank(backup[i+4][0]):
                        straightString += backup[i+4][0]
                        playerList[playerNum].hand[:] = []
                        #print("You Have A Straight!")
                        playerList[playerNum].hand.append(backup[i])
                        playerList[playerNum].hand.append(backup[i+1])
                        playerList[playerNum].hand.append(backup[i+2])
                        playerList[playerNum].hand.append(backup[i+3])
                        playerList[playerNum].hand.append(backup[i+4])
                        return True, straightString
    return False, ""
    
def straightFlush(cards, flushType):
    flushCards = []
    flushType = flushType[0]
    numCards = 0
    for i in range(len(cards)-1):  
        if cards[i][1] == flushType and numCards < 5 and cardRank(cards[i][0])-1 == cardRank(cards[i+1][0]):
            flushCards.append(cards[i])
            numCards += 1
    if numCards == 4:
        flushCards.append(cards[len(cards)-1])
    print(flushCards)
    
    straightString = ""
    if cardRank(flushCards[0][0]) - 1 == cardRank(flushCards[1][0]):
        straightString += flushCards[0] + ", "
        straightString += flushCards[1] + ", "
        if cardRank(flushCards[1][0]) - 1 == cardRank(flushCards[2][0]):
            straightString += flushCards[2] + ", "
            if cardRank(flushCards[2][0]) - 1 == cardRank(flushCards[3][0]):
                straightString += flushCards[3] + ", "
                if cardRank(flushCards[3][0]) - 1 == cardRank(flushCards[4][0]):
                    straightString += flushCards[4]
                    return straightString
    return "Not Straight Flush"
    
def anteUp(pot):
    anteAmount = 25
    for i in playerList:
        i.chips -= anteAmount
        pot += anteAmount
        clients[i.number-1].sendall("You Have Anted {:d} Chips".format(anteAmount).encode('ascii'))
        time.sleep(0.1)
    return pot

def playersRemaining():
    playersLeft = 0
    for i in playerList:
        if i.folded == False:
            playersLeft += 1
    return playersLeft
    
def bettingPhase(pot):
    mustCall = False
    callAmount = 0
    bettingEnded = False
    lastToInitiate = 0
    while bettingEnded == False:
        for i in playerList:
            if lastToInitiate == i.number:
                print("Betting Over")
                bettingEnded = True
                break
            if lastToInitiate == 0:
                lastToInitiate = 1
            if playersRemaining() == 1:
                return pot, True
            if i.folded == False:
                print("Player {:d}'s Turn".format(i.number))
                print("Current Pot: {:d}".format(pot))
                clients[i.number-1].sendall("Current Pot: {:d}".format(pot).encode('ascii'))
                time.sleep(0.1)
                if mustCall == False:
                    loop = True
                    while loop:
                        clients[i.number-1].sendall("Bet/Fold/Check: ".encode('ascii'))
                        betFoldCheck = clients[i.number-1].recv(1024)
                        if betFoldCheck.decode('ascii').upper().startswith("F"):
                            loop = False
                            i.folded = True
                            for x in clients:
                                x.sendall("Player {:d} is Folding!".format(i.number).encode('ascii'))
                            time.sleep(0.1)
                        if betFoldCheck.decode('ascii').upper().startswith("B"):
                            for x in clients:
                                x.sendall("Player {:d} is Betting".format(i.number).encode('ascii'))
                            time.sleep(0.1)
                            loop = False
                            hasBet = False
                            while hasBet == False:
                                clients[i.number-1].sendall("How Much Would You Like to Bet? You Have {:d} Chips: ".format(i.chips).encode('ascii'))
                                loop = False
                                betAmount = clients[i.number-1].recv(1024)
                                betAmount = int(betAmount.decode('ascii'))
                                if i.chips >= betAmount:
                                    i.chips -= betAmount
                                    pot += betAmount
                                    i.betThisTurn = betAmount
                                    callAmount = betAmount
                                    lastToInitiate = i.number
                                    mustCall = True
                                    hasBet = True
                                else:
                                    clients[i.number-1].sendall("You Don't Have That Many Chips".encode('ascii'))
                                    time.sleep(0.1)
                        if betFoldCheck.decode('ascii').upper().startswith("C"):
                            loop = False
                            for x in clients:
                                x.sendall("Player {:d} is Checking".format(i.number).encode('ascii'))
                            time.sleep(0.1)
                        elif loop:
                            clients[i.number-1].sendall("Invalid Entry. Try Again".encode('ascii'))
                            time.sleep(0.1)
                else:
                    loop = True
                    while loop:
                        clients[i.number-1].sendall("Call({:d})/Fold/Raise: ".format(callAmount-i.betThisTurn).encode('ascii'))
                        callFoldRaise = clients[i.number-1].recv(1024)
                        if callFoldRaise.decode('ascii').upper().startswith("F"):
                            loop = False
                            i.folded = True
                            for x in clients:
                                x.sendall("Player {:d} is Folding!".format(i.number).encode('ascii'))
                            time.sleep(0.1)
                        if callFoldRaise.decode('ascii').upper().startswith("C"):
                            loop = False
                            for x in clients:
                                x.sendall("Player {:d} is Calling".format(i.number).encode('ascii'))
                            time.sleep(0.1)
                            currentCallAmount = callAmount - i.betThisTurn
                            if i.chips >= currentCallAmount:
                                i.chips -= currentCallAmount
                                pot += currentCallAmount
                                i.betThisTurn = currentCallAmount
                            else:
                                print("Player {:d} is Going All In!".format(i.number))
                                pot += i.chips
                                i.betThisTurn += i.chips
                                i.chips = 0
                        if callFoldRaise.decode('ascii').upper().startswith("R"):
                            for x in clients:
                                x.sendall("Player {:d} is Raising".format(i.number).encode('ascii'))
                            time.sleep(0.1)
                            hasBet = False
                            loop = False
                            while hasBet == False:
                                clients[i.number-1].sendall("What Would You Like to Raise the Bet to? You Have {:d} Chips: ".format(i.chips).encode('ascii'))
                                raiseAmount = clients[i.number-1].recv(1024)
                                raiseAmount = int(raiseAmount.decode('ascii'))
                                if i.chips >= raiseAmount:
                                    i.chips -= raiseAmount
                                    pot += raiseAmount
                                    i.betThisTurn = raiseAmount
                                    callAmount = raiseAmount
                                    lastToInitiate = i.number
                                    hasBet = True
                                else:
                                    clients[i.number-1].sendall("You Don't Have That Many Chips".encode('ascii')) 
                                    time.sleep(0.1)
                        elif loop:
                            clients[i.number-1].sendall("Invalid Entry. Please Go Enter Again".encode('ascii'))
                            time.sleep(0.1)
    for i in playerList:
        i.betThisTurn = 0
    return pot, False
    
def displayStandings():
    tempList = list(playerList)
    standingsList = []
    while tempList:
        biggest = tempList[0]
        for i in tempList:
            if i.chips > biggest.chips:
                biggest = i
        standingsList.append(biggest)
        tempList.remove(biggest)
    
    for i in standingsList:
        print("Player {:d}: {:d} Chips".format(i.number, i.chips))
        for x in clients:
            time.sleep(0.1)
            x.sendall("Player {:d}: {:d} Chips".format(i.number, i.chips).encode('ascii'))
    
if __name__ == "__main__":
    main()             