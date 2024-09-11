# savills_vn
Reverse Engineering Savills Property Cube App

This is the reverse engineering of Savills Property Cube App.
There are a lot of security bugs in this app as well to name a few you can get all other User Infos ( other users in your Condo) ( including username, email.phone, unit Number)
as long as you can login to the app

Base on not protecting the user role, once a user can login to the system, it can query other user's information by:

1. Through the Booking system

or 

2. Through the Fee Management System


My purpose for the start is only implementing an automatic Booking request to book a tennis court for my kid.

Right now, the way Savills control the booking is very strict. It only allows 1 booking per week and can only book 1 month in advance

so instead of having to wake up at 12am last day of every month, as a software engineer, I decided to automate the booking process :D
