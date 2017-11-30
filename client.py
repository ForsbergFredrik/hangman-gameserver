#!/usr/bin/env python3
from socket import *
import sys


def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf:
            return None
        buf += newbuf
        count -= len(newbuf)
    return buf


def recv_message(sock):
    msg_flag_byte = recvall(sock, 1)
    if not msg_flag_byte:
        # Server has closed the connection
        return -1, None, None, None
    else:
        msg_flag = int.from_bytes(msg_flag_byte, byteorder='big')
        if msg_flag == 0:
            # This is a control message
            word_length_byte = recvall(sock, 1)
            if not word_length_byte:
               # Server unexpectedly closed the connection
               return -2, None, None, None
            word_length = int.from_bytes(word_length_byte, byteorder='big')
            num_incorrect_byte = recvall(sock, 1)
            if not num_incorrect_byte:
               # Server unexpectedly closed the connection
               return -2, None, None, None
            num_incorrect = int.from_bytes(num_incorrect_byte, byteorder='big')
            data = recvall(sock, word_length + num_incorrect)
            if not data:
               # Server unexpectedly closed the connection
               return -2, None, None, None
            return msg_flag, data, word_length, num_incorrect
        else:
            # This is a message packet
            data_length = msg_flag
            data = recvall(sock, data_length)
            if not data:
               # Server unexpectedly closed the connection
               return -2, None, None, None
            else:
               return msg_flag, data, None, None


def main():

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    # Create TCP socket
    client_socket = socket(AF_INET, SOCK_STREAM)

    # Connect to Server
    client_socket.connect((server_ip, server_port))

    # answer = input("Ready to start game? (y/n):")
    data = ""
    answer = "-1"
    while answer != "y" and answer != "n":
        answer = input("Ready to start game? (y/n):")
        if answer == "y":
            data = create_message("")
            client_socket.send(data)
            start_game(client_socket)
        elif answer == "n":
            client_socket.close()

    # Close client socket
    client_socket.close() 

def start_game(client_socket):

    state = True

    while state:
        # Extract data from server
        msg_flag, data, word_len, wrong_guesses = recv_message(
            client_socket)
        if (msg_flag == -1):
            print("Error! No connection to server.")
            break
        if (msg_flag == -2):
            print("Error! Server has unexpectedly closed the connection.")
            break



        # If packet contains game information
        if (msg_flag == 0):
            word = data[:word_len].decode()
            incorrect_guesses = data[word_len:].decode()

            # Print information about current game state
            print("Word: {}\nIncorrect Guesses: {}\n".format(
                " ".join(word), " ".join(incorrect_guesses)))

            if "_" in word and wrong_guesses != 6:
                # Let the client enter a letter
                guess = input("Letter to guess: ")

                # Make sure the letter is well formatted
                guess = letter_check(guess, incorrect_guesses, word)

                # Make sure letter are in lowercase
                guess = guess.lower()

                # Create message to send to server
                msg = create_message(guess)

                # Send message to server
                client_socket.send(msg)

        # If packet contains control information
        elif (msg_flag != 0):
            # Message with flag != 0
            content = data
            content = content.decode()

            if (content == "Congrats you won" or content == "Game Over"
                    or content == "Server-Overloaded"):
                print(content)
                state = False


def letter_check(letter, guessed, word):
    guess = letter

    while not guess.isalpha() or len(guess) != 1 or guess in guessed or guess in word:
        if not guess.isalpha() or len(guess) != 1:
            # Inform the user what went wrong
            print("Error! Please guess a letter.")
            # Let the client enter a letter
            guess = input("Letter to guess:")

        if guess in guessed or guess in word:
            # Inform the user what went wrong
            print(
                "Error! Letter {} has been guessed before, please guess another letter.".
                format(guess.upper()))
            # Let the client enter a letter
            guess = input("Letter to guess:")

    return guess


# Method to create messages exchanges between client and server
def create_message(guess):
    arr = bytes()

    if len(guess) == 0:
        arr = bytes([len(guess)])
    else:
        binary_msg_flag = bytes([len(guess)])
        binary_word = bytes(guess.encode())

        arr = binary_msg_flag + binary_word

    return arr


if __name__ == "__main__":
    main()

