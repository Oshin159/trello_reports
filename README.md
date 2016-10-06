This project deals with generating project reports from trello automatically

The Trello index has different documentation in Elastic Search
The script will throw an error in case a key is not retrievable and that will we directed to the screen

Card:
"Type":"Card" #This represents that the document is of the type card
 "BoardID": Id of the board the card belongs to
 "BoardName": Name of the board the card belongs to
 "ListID": Id of the list the card belongs to currently
 "ListName": Name of the list the card belongs to currently.
 "CardID": Id of the card
 "Members": List of the fullName of the Members
 "Labels": List of the names of the Labels currently associated with the card
 "Name": Current ame of the card
 "Description": Description of the card
 "ShortURL": ShortUrl of the card,
 "Status": status of the card -open/closed,
 "DueDate": Due Date of the Card,
 "LastActivity": Date of last activity on the card
 "Date":The date of creation of the card

Action Card:
  "Type":"Action"  #This represents that the document is of the type Action
  "ActionType": This is the type of the action(updateCard,createCard,commentCard)
  "ActionId": This is the id of the action
  "Date": This is the date of the occuring of the action:
   for updateCard it represents when the card has b
  "MemberCreator": action["memberCreator"]["fullName"],
  "CardId": action["data"]["card"]["id"],
  "CardName": action["data"]["card"]["name"],
  "BoardName": action["data"]["board"]["name"],
  "BoardId": action["data"]["board"]["id"],

For action card of the type listed below there are additional fields:
1)ActionType="updateCard" :
   "ValueEdited":This is the value of that is edited,can be either LIST,NAME or DESCRIPTION
   #updation of list for a card implied movement of the list from one card to another
   "ValueBefore":This is the value before the action occured
   "ValueAfter":This is the value after the action occured
2)ActionType="commentCard":
    "ListName":The name of the list in which the card is currently
    "ListId":The id of the list the card currently belongs to
    "CommentText":The text of the comment inserted(in unicode)
3)ActionType="createCard":
    "ListName":The name of the list in which the card is currently
    "ListId":The id of the list the card currently belongs to



Logs:
1)WARNING logs:
    *)In case a createCard Action is not found for any of the Card
    *)In case the current list in which the card exists is not the one in which the card was last moved.
2)CRITICAL logs:
    *)Action Type not handled for any particular card
    *)Trello api limit that is 100 req in 10 sec is hit
    *)Unable to reach elastic search
    In the last two cases the system retries 5 times before giving up
3)ERROR logs:
    *)If a particular document could not be inserted to elastic search
    *)If any required key is not found in the data returned from elastic search

Script raises error in case
    *)Max retries done for elastic search or trello
    *)If for trello method other then GET is specified

File structure of the project:

----->The script takes in 3 command line argument that is the url on which the elastic search host is running,i.e.
http://host:port,API_KEY and API_TOKEN

Run the script using
python scriptname http://host:port API_KEY API_TOKEN

----->The bash script will take 2 arguments
Argument 1:elastic search host as specified in the format above
Argument 2:the name of the python script to be run
./populate_index elastic_host:port scriptname

----->config.txt
contains the API key and API token
in the form

API_KEY "...."
API_TOKEN   "..."

separated by tab

There is a sample config.txt provided named as sample_config.txt
after entering your API key do
mv sample_config.txt config.txt
