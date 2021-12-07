Sofia Giannuzzi and Dacha Thurber Final Project for CS50, fall 2021
 
Before running, run the following commands to install necessary packages:
 pip3 install cs50
 pip3 install Flask
 pip3 install Flask-Session
 pip3 install matplotlib
Also ensure you have the following installed on your machine:
<<<<<<< HEAD
  python3
  sqlite3
  NodeJS

To run, copy all files into a directory.  Within that directory run the command line commands:

% export FLASK_APP=app
% flask run

This will launch a flask server at a given link printed to the terminal:

INFO:  * Running on YOUR_LINK (Press CTRL+C to quit)

Follow the link in a browser to view the Snoozer website.


At first, you will be brought to a standard login page with an option to register if you have yet to make an account.  Once you have registered and logged in, you will be brought to the main website.

Once viewing the main website, you will automatically be brought to the homepage (accessaile also by clicking the Snoozer icon in the top navbar).  The homepage is automatically set to the wakeup page in the morning, the sleep logging page in the midday, and the bedtime page in the evening.  Each of these pages is also accessible in the top navbar.

On the wakeup page, you will find a morning greeting with your name, a new affirmation generated each day, the daily weather for your location and links to three morning news sources.

On the report page, you will find three fields to fill out (today's date, bedtime, and wakeup), which can be populated using their associated dropdown menus and submitted for each night's sleep.  This is where you log your own data each morning or retrospectively.

On the bedtime page, you will also find a greeting with your name and a sheep-counting video, because the best way to fall asleep is to watch ruminant mammals perform mindless tasks.

On the data page, you will find filters to apply to other user's data when visualizing comparisons against your own.  Customize what data you see in the graphs plotted against your own by selecting values from the fields' dropdown menus.  Each filter adds specificity, and in the case of contradiction, more specific filters will take precedence over less specific filters (i.e. if you select to view the data of a particular friend, you will see that data regardless of the more general filters).  No field is required except the Number of Days, which takes an integer input and will automatically round down to the number of datapoints you have entered for yourself. (N.B. to remove the ambiguity of bedtime events before/after midnight, all bedtime data is plotted against the date of the next morning.) (N.B. as our website does not yet have a global user base, data from many countries and states in the US is not yet entered.  To view the functionality of the page, try comparing your data to any of your friends, or to users in Canada, South Africa, Israel, and in the United States (specifically, NH, CT, MT, and MA) as well as users of all gender identities from the last seven days.)

On the friends page, you will find a dropdown menu of other users who you can befriend to view their data.
=======
 python3
 sqlite3
 NodeJS
 
To run, copy all files into a directory.  Within that directory run the command line commands:
 
% export FLASK_APP=app
% flask run
 
This will launch a flask server at a given link printed to the terminal:
 
INFO:  * Running on YOUR_LINK (Press CTRL+C to quit)
 
Follow the link in a browser to view the Snoozer website.
 
 
At first, you will be brought to a standard login page with an option to register if you have yet to make an account.  Once you have registered and logged in, you will be brought to the main website.
 
Once viewing the main website, you will automatically be brought to the homepage (accessible also by clicking the Snoozer icon in the top navbar).  The homepage is automatically set to the wakeup page in the morning, the sleep logging page in the midday, and the bedtime page in the evening.  Each of these pages is also accessible in the top navbar.
 
On the wakeup page, you will find a morning greeting with your name, a new affirmation generated each day, the daily weather for your location and links to three morning news sources.
 
On the report page, you will find three fields to fill out (today's date, bedtime, and wakeup), which can be populated using their associated dropdown menus and submitted for each night's sleep.  This is where you log your own data each morning or retrospectively.
 
On the bedtime page, you will also find a greeting with your name and a sheep-counting video, because the best way to fall asleep is to watch ruminant mammals perform mindless tasks.
 
On the data page, you will find filters to apply to other user's data when visualizing comparisons against your own.  Customize what data you see in the graphs plotted against your own by selecting values from the fields' dropdown menus.  Each filter adds specificity, and in the case of contradiction, more specific filters will take precedence over less specific filters (i.e. if you select to view the data of a particular friend, you will see that data regardless of the more general filters).  No field is required except the Number of Days, which takes an integer input and will automatically round down to the number of datapoints you have entered for yourself. (N.B. to remove the ambiguity of bedtime events before/after midnight, all bedtime data is plotted against the date of the next morning.) (N.B. As our website does not yet have a global user base, data from many countries and states in the US is not yet entered.  To view the functionality of the page, try comparing your data to any of your friends, or users in Canada, South Africa, Israel, and in the United States (specifically, NH, CT, MT, and MA) as well as users of all gender identities from the last seven days.)
 
 
On the friends page, you will find a dropdown menu of other users who you can befriend to view their data.
>>>>>>> 2f600db39a17376427c83fe5a028ed263c860eb7
