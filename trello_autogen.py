"""Module fetch data about cards from elastic search and then
Name:auto_report_trello.py
Author:Oshin Agarwal
 """

import logging
from time import sleep
from threading import Thread
from workdays import networkdays
from datetime import datetime
import sys
from elasticsearch import Elasticsearch
import traceback
import requests
import json

# API key and API token is the one generated from trello
API_KEY = sys
API_TOKEN = "3f1a00106e7b04af9aec297957892b99a2ae45bae8fcec4ef94fa94443ce4b5c"
NOT_FOUND = "Not found"
fileName='trello.log'
index = "trello-%s" % (datetime.utcnow().strftime("%Y.%m.%d"))
#elastic Id is the unique Id of the elastic search document
elasticID = 0
#this is for no. of uninserted documents
uninserted_Docs = 0
logging.basicConfig(filename=fileName, level=logging.WARNING, filemode="w")


# different doctype of elastic search cards,createCard,updateCard,commentCard

# a members full name has been taken account everywhere not his username
# class for connection to elastic search
class ElasticSearchConnection(object):
    def __init__(self):
        self.now = datetime.utcnow()
        try:
            self.conn = Elasticsearch(hosts=sys.argv[1])
        except IndexError:
            print "Enter the elasticsearch host as command line argument"
            sys.exit(0)
        self.index = "trello-%s" % (datetime.utcnow().strftime("%Y.%m.%d"))
        pass

    def indexDocument(self, doctype, document):
        document["Timestamp"] = self.now
        for x in range(5):
            try:
                return self.conn.index(index=self.index, doc_type=doctype, body=document)
            except:
                traceback.print_exc()
                pass


# ES_CONN=ElasticSearchConnection()

def api(method, endpoint, data=dict()):
    """A function to query trello api.
            It makes 5 different attempts to in case the limit for trello api is
            hit and sleeps for 1 sec as a brute force attempt

       Args:
            method(String):Accepts none other method than GET as of now
            endpoint(String):the end point as specified in trello documentation
            data(dictionary):Any additional data that is to provided like some filters

       Returns:
            returns the response in json format as given by trello api

       Raises:
           Max retries failed in case the no. of retries for trello exceed 5
           If any method is not implemented
       """
    # logging.info("[Trello:%s] Fetching %s", method, endpoint)
    data.update({"key": API_KEY, "token": API_TOKEN})
    url = "https://api.trello.com/1/%s" % (endpoint)
    if method == "GET":
        url += "?"
        url += '&'.join(["%s=%s" % (k, v) for k, v in data.items()])
        for attempt in range(5):
            try:
                response = requests.get(url)
                return response.json()
            except:
                sleep(1)
                logging.critical("Exception: %s", response.text)
        raise Exception("Failure: Max retries exceeded for %r" % url)
    raise Exception("Not implemented")


def create_uri(uri, index_name, type):
    """Function to create url for elastic search

       Args:
          uri(String):url as http://host:port
          index_name:index name in elastic search
          type(String):type of the elastic search document

       Returns:
            returns url for elastic search

       """
    global elasticID
    elasticID = elasticID + 1
    return uri.strip() + "/" + index_name + "/" + type + "/" + str(elasticID) + "?pretty"


def curl_query(uri, index_name, query_json, type):
    """Function to curl query to elastic search and return response

       Args:
          uri(String):url as http://host:port
          index_name:index name in elastic search
          type(String):type of the elastic search document
          query_json:the data to be inserted

       Returns:
            response from the query

       Raises:
           Max retries failed in case the no. of retries for trello exceed 5

       """
    global uninserted_Docs
    query_st = query_json
    curl_uri = create_uri(uri, index_name, type)
    for attempt in range(5):
        try:
            response = requests.put(curl_uri, data=query_st)
            results = response.content
            if results.find('false') > -1:
                uninserted_Docs = uninserted_Docs + 1
                #if type=='cards':
                 #   logging.error("Cannot insert in index CARDID %s"%query_json['CardID'] )
                #else:
                #    logging.error("Cannot insert in index ACTIONID %s" % query_json['ActionID'])
                logging.error("Cannot  insert %s ",query_json)
            return
        except:
            logging.critical("Exception %s", response.text)
    raise Exception("Failure: Max retries exceeded for Connecting to Elastic search")


def get_my_organizations():
    """Function to get the organization associated with trello api key and token

        Args:
            None

        Returns:
            Id of the organizaton

        """
    my_info = api("GET", "members/me")
    my_orgs = my_info["idOrganizations"]
    return my_orgs


def get_members(board_id):
    """Function to get members of a board

        Args:
            board_id(string):Id of the board whose members are to be retrived

        Returns:
            Dictionary with key as member id and value as member json returned from trello

        """
    members = api("GET", "board/%s/members" % board_id)
    return {m["id"]: m for m in members}


def get_boards(org_id):
    """Function to get boards of an organization

        Args:
            org_id(string):Id of the organization whose boards are to be retrived

        Returns:
            Dictionary with key as board id and value as board json returned from trello
        """

    boards = api("GET", "organizations/%s/boards" % org_id)
    return {b["id"]: b for b in boards}


def get_board_lists(board_id):
    """Function to get lists of a board

        Args:
            board_id(string):Id of the board whose lists are to be retrived

        Returns:
            Dictionary with key as list id and value as list json returned from trello
        """
    lists = api("GET", "boards/%s/lists" % board_id)
    return {l["id"]: l for l in lists}


def get_board_cards(board_id):
    """Function to get cards of a board

        Args:
            board_id(string):Id of the board whose cards are to be retrived

        Returns:
            Dictionary with key as card id and value as card json returned from trello
        """
    cards = api("GET", "boards/%s/cards" % board_id, {"fields": "closed,dateLastActivity,\
    ,desc,due,idLabels,idBoard,idList,idMembers,\
    ,name,pos,shortUrl,url,labels"})
    return {card["id"]: card for card in cards}


def get_card_actions(card_id, data=dict()):
    """Function to get actions associated with a card

        Args:
            card_id(string):Id of the card whose boards are to be retrived
            data(dictionary):additional filters to be passed to api function

        Returns:
            response as given by elastic search
        """
    actions = api("GET", "cards/%s/actions" % card_id, data)
    return actions


def get_board_actions(board_id, data=dict()):
    """Function to get actions associated with a board

           Args:
               card_id(string):Id of the card whose boards are to be retrived
               data(dictionary):additional filters to be passed to api function

           Returns:
               response as given by elastic search
           """
    actions = api("GET", "boards/%s/actions" % board_id, data)
    return actions


def send_elasticSearch(comm, type):
    """Function to send data to elastic search

        Args:
            card_id(string):Id of the card whose boards are to be retrived
            data(dictionary):additional filters to be passed to api function

        Returns:
            response as given by elastic search
        """
    # print ES_CONN.indexDocument(doctype=type, document=comm)
    global index
    curl_query(sys.argv[1], index, json.dumps(comm), type)


def sanitize_card(card, lists, board, members):
    """Function to parse the card data as returned by trello and  send to elastic search

        Args:
            card(dictionary):card data dictionary as returned by trello for the board
            lists(dictionary):lists as given by get_board_lists function for board
            board(dictionary):board data dictionary of the board to which the card belongs
            members(dictionary):members as given by get_board_members

        Returns:
            nothing
            """
    status = "open"
    if card['closed']:
        status = "closed"
    current_time = datetime.now()
    created_date = datetime.fromtimestamp(int(card["id"][0:8], 16))
    card_life = networkdays(created_date, current_time)
    iso_created_date = datetime.isoformat(created_date)
    try:
        comm = {
            "Type": "Card",
            "BoardID": card["idBoard"],
            "BoardName": board["name"],
            "ListID": card["idList"],
            "ListName": lists.get(card["idList"], {}).get("name", NOT_FOUND),
            "CardID": card["id"],
            "Members": [members[m_id]["fullName"] for m_id in card["idMembers"]],
            "Labels": [l['name'] for l in card["labels"]],
            "CardName": card["name"],
            "Description": card["desc"],
            "ShortURL": card["shortUrl"],
            "Status": status,
            "DueDate": card['due'],
            "CardLife": card_life,
            "Date": iso_created_date,
            "LastActivity": card["dateLastActivity"],
        }
    except KeyError as k:
        logging.error("Unable to find key %s in card %s" % (str(k), card['id']))
    send_elasticSearch(comm, "cards")


def sanitize_actionCard(action, card, lists, board, members):
    """Function to parse the common action data as returned by trello

            Args:
                action(dictionary):action data dictionary as returned by trello
                card(dictionary):card data dictionary as returned by trello for the board
                lists(dictionary):lists as given by get_board_lists function for board
                board(dictionary):board data dictionary of the board to which the card belongs
                members(dictionary):members as given by get_board_members

            Returns:
                common data for all action
                """
    try:
        t = {
            "Type": "Action",
            "ActionName": action["type"],
            "ActionID": action["id"],
            "Date": action["date"],
            "Members": action["memberCreator"]["fullName"],
            "CardID": action["data"]["card"]["id"],
            "CardName": action["data"]["card"]["name"],
            "BoardName": action["data"]["board"]["name"],
            "BoardID": action["data"]["board"]["id"],
        }
    except KeyError as k:
        logging.error("Unable to find key %s for action %s" % (str(k), action["id"]))
    except TypeError:
        print action
    else:
        return t


def sanitize_updateCard_idList(action, card, lists, board, members, data):
    """Function to parse the updatecard for change in list
     action data as returned by trello and  send to elastic search

            Args:
                action(dictionary):action data dictionary as returned by trello
                card(dictionary):card data dictionary as returned by trello for the board
                lists(dictionary):lists as given by get_board_lists function for board
                board(dictionary):board data dictionary of the board to which the card belongs
                members(dictionary):members as given by get_board_members
                data(dictionary):any additional data to be added to elastic search document

            Returns:
                nothing

        """
    comm = sanitize_actionCard(action, card, lists, board, members)
    try:
        comm["ValueEdited"] = 'List'
        comm["ValueBefore"] = action['data']['listBefore']['name']
        comm['ValueAfter'] = action['data']['listAfter']['name']
    except KeyError as k:
        logging.error("Unable to find key %s for action %s" % (str(k), action["id"]))
    comm.update(data)
    send_elasticSearch(comm, "updateCard")


def sanitize_updateCard_desc(action, card, lists, board, members, data):
    """Function to parse the updatecard for change in description
         action data as returned by trello and  send to elastic search

            Args:
                action(dictionary):action data dictionary as returned by trello
                card(dictionary):card data dictionary as returned by trello for the board
                lists(dictionary):lists as given by get_board_lists function for board
                board(dictionary):board data dictionary of the board to which the card belongs
                members(dictionary):members as given by get_board_members
                data(dictionary):any additional data to be added to elastic search document

            Returns:
                nothing

            """
    comm = sanitize_actionCard(action, card, lists, board, members)
    try:
        comm['ValueEdited'] = 'Name'
        comm['ValueBefore'] = action['data']['old']['desc']
        comm['ValueAfter'] = action['data']['card']['desc']
    except KeyError as k:
        logging.error("Unable to find key %s for action %s" % (str(k), action["id"]))
    comm.update(data)
    send_elasticSearch(comm, "updateCard")


def sanitize_updateCard_name(action, card, lists, board, members, data):
    """Function to parse the updatecard for change in name
         action data as returned by trello and  send to elastic search

            Args:
                action(dictionary):action data dictionary as returned by trello
                card(dictionary):card data dictionary as returned by trello for the board
                lists(dictionary):lists as given by get_board_lists function for board
                board(dictionary):board data dictionary of the board to which the card belongs
                members(dictionary):members as given by get_board_members
                data(dictionary):any additional data to be added to elastic search document

            Returns:
                nothing

            """
    comm = sanitize_actionCard(action, card, lists, board, members)
    try:
        comm['ValueEdited'] = 'Desc'
        comm['ValueBefore'] = action['data']['old']['name']
        comm['ValueAfter'] = action['data']['card']['name']
    except KeyError as k:
        logging.error("Unable to find key %s for action %s" % (str(k), action["id"]))
    comm.update(data)
    send_elasticSearch(comm, "updateCard")


def sanitize_commentCard(action, card, lists, board, members, data):
    """Function to parse the comments action data as returned
    by trello and  send to elastic search

        Args:
            action(dictionary):action data dictionary as returned by trello
            card(dictionary):card data dictionary as returned by trello for the board
            lists(dictionary):lists as given by get_board_lists function for board
            board(dictionary):board data dictionary of the board to which the card belongs
            members(dictionary):members as given by get_board_members
            data(dictionary):any additional data to be added to elastic search document

        Returns:
            nothing

        """
    comm = sanitize_actionCard(action, card, lists, board, members)
    comm['CommentText'] = action['data']['text']
    try:
        comm['ListName'] = action['data']['list']['name']
    except KeyError:
        comm['ListName'] = lists.get(action['data']['list']['id'], {}).get("name", NOT_FOUND),
    try:
        comm['ListId'] = action['data']['list']['id']
    except KeyError:
        comm['ListId'] = ""
        logging.error("ListId not found for %s actionCard " % action['id'])
    comm.update(data)
    send_elasticSearch(comm, "commentCard")


def sanitize_createCard(action, card, lists, board, members, data):
    """Function to parse the create card action data as returned
        by trello and  send to elastic search

            Args:
                action(dictionary):action data dictionary as returned by trello
                card(dictionary):card data dictionary as returned by trello for the board
                lists(dictionary):lists as given by get_board_lists function for board
                board(dictionary):board data dictionary of the board to which the card belongs
                members(dictionary):members as given by get_board_members
                data(dictionary):any additional data to be added to elastic search document

            Returns:
                nothing

            """
    comm = sanitize_actionCard(action, card, lists, board, members)
    try:
        comm['ListName'] = action['data']['list']['name']
    except KeyError:
        comm['ListName'] = lists.get(action['data']['list']['id'], {}).get("name", NOT_FOUND),
    try:
        comm['ListID'] = action['data']['list']['id']
    except KeyError:
        comm['ListID'] = ""
        logging.error("ListId not found for %s actionCard " % action['id'])
    comm.update(data)
    send_elasticSearch(comm, "createCard")
    return action[
        "date"]  # this works since we are currently querying per card so every card will have only one createCard


def sanitize_action(actions, card, lists_in_boards, board, members, data):
    """Function to find the action type and send to parse data accordingly

            Args:
                actions(dictionary):list of action data dictionary as returned by trello
                card(dictionary):card data dictionary as returned by trello for the board
                lists_in_boards(dictionary):lists as given by get_board_lists function for board
                board(dictionary):board data dictionary of the board to which the card belongs
                members(dictionary):members as given by get_board_members
                data(dictionary):any additional data to be added to elastic search document

            Returns:
                0 in case there is a name error

            """
    for action in actions:
        if action['type'] == 'createCard':
            created_date = sanitize_createCard(action, card, lists_in_boards, board, members, data)
        elif action['type'] == 'updateCard':
            if 'listBefore' in action['data']:
                sanitize_updateCard_idList(action, card, lists_in_boards, board, members, data)
                if card['dateLastActivity'] == action['date'] and card['idList'] != action['data']['listAfter']['id']:
                    logging.warning(
                        "[Last update Action] %s and card data %s inconsistent]" % (action['id'], card['name']))
            elif 'name' in action['data']['old']:
                sanitize_updateCard_name(action, card, lists_in_boards, board, members, data)
            elif 'desc' in action['data']['old']:
                sanitize_updateCard_desc(action, card, lists_in_boards, board, members, data)
            else:
                logging.critical("[UpdateCard] other than name,description or list %s", card["id"])
        elif action['type'] == 'commentCard':
            sanitize_commentCard(action, card, lists_in_boards, board, members, data)
        else:
            logging.critical("[ActionType] NOT FOUND [CARD] %s" % card["id"])
    try:
        created_date
    except NameError:
        logging.warning("[createdCard ACTION] NOT FOUND [CARD] %s %s %s " % (card["id"], card["name"], board['name']))
        return 0


def worker(board_id, board):
    """Worker thread function for each board which will get its members,lists,
    cards  and send their data after parsing to elastic search

            Args:
                board(dictionary):board data dictionary of the board to which the card belongs
                board_id(string):id of the board

            Returns:
                nothing

            """
    members = get_members(board_id)
    cards = get_board_cards(board_id)
    lists_in_boards = get_board_lists(board_id)
    for card_id, card in cards.items():
        status = "open"
        if card['closed']:
            status = "closed"
        #if a card is closed the corresponding action is closed as well
        data = {'Status': status}
        actions = get_card_actions(card_id, {'filter': 'createCard,updateCard:idList,updateCard:name,\
        ,updateCard:desc,commentCard'})
        sanitize_action(actions, card, lists_in_boards, board, members, data)
        sanitize_card(card, lists_in_boards, board, members)


def main():
    """Main function :
    retrives organization's boards and runs threads for each of them at the interval of 5sec"""
    threads = []
    for orgId in get_my_organizations():
        boards = get_boards(orgId)
        for board_id, board in boards.items():
            print "-----------%s-------------" % board["name"]
            if board['closed']:
                continue
            t = Thread(target=worker, args=(board_id, board))
            sleep(5)
            t.start()
            threads += [t]


if __name__ == '__main__':
    if len(sys.argv)==1:
        raise Exception("ElasticSearch host not provided")
    main()
    if uninserted_Docs:
        print "%s no. of docs cannot be inserted\nCheck error logs in %s\n" % (uninserted_Docs,fileName)
