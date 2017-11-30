#!/usr/bin/env python3

from socket import *
import threading
import random
import sys

# This class represent the Hangman game
class Game:

    words = []

    # Initiate the game and randomly select a word
    def __init__(self, word_list):

        Game.words = word_list

        self.sr = random.SystemRandom()
        self.nr_of_guesses = 0
        self.answer = list(self.sr.choice(Game.words))
        self.word = []

        for letter in range(len(self.answer)):
            self.word.append("_")

        self.guesses = []

    def get_word(self):
        return self.word

    def get_answer(self):
        return self.answer

    # Get number of wrong guesses
    def get_nr_of_guesses(self):
        return self.nr_of_guesses

    def insert_letter(self, guess):
        for index, letter in enumerate(self.answer):
            if(letter == guess):
                self.word[index] = guess

    def make_guess(self, guess):
        #guess = guess.upper()
        if guess in self.answer and guess not in self.guesses:
            self.insert_letter(guess)
            self.guesses.append(guess)
        elif(guess not in self.guesses):
            self.nr_of_guesses += 1
            self.guesses.append(guess)
        else:
            self.nr_of_guesses += 1

    def get_guesses(self):
        return self.guesses

    def check_if_win(self):
        letter = "_"
        flag = True
        if(letter in self.word):
            flag = False
        return flag

    def get_word_len(self):
        return len(self.word)

#**********************************************************************

# Thread
class MyThread(threading.Thread):
    def __init__(self, connection_socket, addr, word_list):
        threading.Thread.__init__(self)
        self.connection_socket = connection_socket
        self.addr = addr
        self.word_list = word_list

    def start_game(self, game):
        while True:

            # Create message with game information to client.
            # Message will be organized in the correct order in the create_game_control_message method.
            # Arguments passed in different order to make use of default parameters
            msg = create_game_control_message(0, game.get_word(), game.get_guesses(), game.get_word_len(),
                                                  game.get_nr_of_guesses())
            # Send message to client
            self.connection_socket.send(msg)

            # Receive data from client
            rtv = self.connection_socket.recv(1024)

            rtv = rtv.decode()
            # print("Letter from client: {}".format(rtv[1]))

            # Make a guess
            game.make_guess(rtv[1])

            # Check if win
            if (game.check_if_win()):
                msg = create_game_control_message(0, game.get_word(), game.get_guesses(), game.get_word_len(),
                                                  game.get_nr_of_guesses())
                #print("Message: {}".format(msg))
                # Send message to client
                self.connection_socket.send(msg)

                #print("Congrats you won!")
                msg = create_game_control_message(len("Congrats you won"), "Congrats you won")
                self.connection_socket.send(msg)
                break

            # Check if lose
            if (game.nr_of_guesses == 6):
                msg = create_game_control_message(0, game.get_word(), game.get_guesses(), game.get_word_len(),
                                                  game.get_nr_of_guesses())
                # print("Message: {}".format(msg))
                # Send message to client
                self.connection_socket.send(msg)

                # print("You lost...")
                # Send control message "LOSE"
                msg = create_game_control_message(len("Game Over"), "Game Over")
                self.connection_socket.send(msg)
                break

    def run(self):

        # Check if client is ready to start the game
        data = self.connection_socket.recv(1024)
        if data and data[0] == 0:
            # Create an instance of the game
            game = Game(self.word_list)

            # Start the game
            self.start_game(game)

        print("Closing connection {}".format(self.addr))
        # Closing the connection
        self.connection_socket.close()


# Creates control information to server
def create_game_control_message(msg_flag, word, guesses = None, word_length = None, num_guess = None):

    # If flag = 0
    arr = bytes()
    if(msg_flag == 0):

        binary_msg_flag = bytes([msg_flag])
        binary_word_length = bytes([word_length])
        binary_num_guess = bytes([num_guess])
        word = "".join(word)
        binary_word = bytes(word.encode())
        guesses = "".join(guesses)

        # List comprehension to get incorrect guesses
        incorrect_guesses = [x for x in guesses if x not in word]
        incorrect_guesses = "".join(incorrect_guesses)
        binary_guesses = bytes(incorrect_guesses.encode())

        arr = binary_msg_flag + binary_word_length + binary_num_guess + binary_word + binary_guesses

    else:
        # If flag != 0
        #pack_data = pack("i" + word_length * "s", msg_flag, word)
        binary_msg_flag = bytes([msg_flag])
        binary_word = bytes(word.encode())

        arr = binary_msg_flag + binary_word

    return arr

#************************************************************'
def main():
    file_name = "wordlist.txt"

    word_list = []
    if(len(sys.argv) == 2):
        word_list = [line.strip() for line in open(file_name, "r")]

    elif(len(sys.argv) == 3):
        file_name = sys.argv[2]
        word_list = [line.strip() for line in open(file_name, "r")]
        word_list = word_list[1:]



    server_port = int(sys.argv[1])
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('', server_port))

    server_socket.listen(3)
    #print("Server is up and running!")

    while True:
        connection_socket, addr = server_socket.accept()

        print("Connection from {} ".format(addr))
        # main process plus 3 threads currently accepted
        if (threading.activeCount() < 4):
            hangman = MyThread(connection_socket, addr, word_list)
            hangman.start()
        else:

            # TODO log server overloaded in command line
            # Send “server-overloaded” message
            msg = create_game_control_message(len("Server-Overloaded"), "Server-Overloaded")
            connection_socket.send(msg)
            connection_socket.close()

            print("Closing connection {}".format(addr))
        
        #print("Active threads: {} ".format(threading.activeCount()))


if __name__ == "__main__":
    main()



