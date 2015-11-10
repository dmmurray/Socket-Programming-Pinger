Dan Murray
dmmurray@wpi.edu

# Socket-Programming-Pinger
An implementation of an ICMP pinger

I wrote my code and tested it in Ubuntu 15.10.

In order to run my code, you must download Python 2.7.10.
Once this is installed, open a terminal and run the command
"sudo apt-get install python-numpy". This will prompt you to enter
your sudo password. This is simply your root password for your
Ubuntu. Once you have installed python and numpy, open a terminal,
cd to the folder in which you have saved ICMPpinger.py, and run the
following command: "chmod +x ICMPpinger.py"

Now that you have done this, still in the same directory, you run my
program by entering the command "sudo python ICMPpinger.py". It will
prompt your sudo password again, and then the program will run. You
will see ">" at the beginning of a line and a cursor. Here, you type
in the address you wish to ping, a space, and the number of times you
wish to ping it. Alternatively, if you don't add a number of times you
want to ping it, it will ping indefinitely until you kill the program.
When the program finishes, regardless of the terms under which it
finished, it will provide you with a summary of the program execution.