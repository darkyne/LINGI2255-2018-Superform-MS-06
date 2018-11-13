import json
import string
import traceback
import random

from flask import request, render_template
from linkedin import linkedin  # from python3-linkedin library

#########################
## credentials reading ##
#########################
import configparser
from pathlib import Path
import sys

FIELDS_UNAVAILABLE = ['Title', 'Description']

CONFIG_FIELDS = []  # Unused for now. But could be used to refresh dynamically the access token


########################
## template rendering ##
########################

def linkedin_plugin(id, c, config_fields):
    """
    Launched by channels.configure_channel(id) when the configure page
    is reached and the channel is from the LinkedIn module. It creates
    the redirect_link which is used in the linkedin_configuration.html
    and calls the render_template() function.
    :param id: id of the channel; used to create the redirect_link
    :param c: the channel object; used to pass the information to the template
    :param config_fields: configuration fields; used to pass the information to the template
    :return: creates the template
    """
    state = "id_" + str(id) + "rest_" + id_generator()
    return_url = 'http://localhost:5000/configure/linkedin'
    client_id = "no client id"

    try:
        client_id = get_client_id()
    except FileNotFoundError:
        print(
            "linkedin.ini file not found. Please check that the linkedin.ini "
            "file is placed in the superform/plugins folder.")

    redirect_link = "https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=" \
                    + client_id + "&redirect_uri=" + return_url + "&state=" + state
    return render_template("linkedin_configuration.html",
                           channel = c,
                           config_fields = config_fields,
                           redirect = redirect_link)


############################
## authentication process ##
############################

def get_linkedin_authentication():
    """
    Get the access to the LinkedIn account and links it to the python3-linkedin library
    :return: the authentication object created by the python3-linkedin library
    """
    try:
        client_id = get_client_id()
    except FileNotFoundError:
        print(
            "linkedin.ini file not found. Please check that the linkedin.ini "
            "file is placed in the superform/plugins folder.")
        client_id = None
    try:
        client_secret = get_client_secret()
    except FileNotFoundError:
        print(
            "linkedin.ini file not found. Please check that the linkedin.ini "
            "file is placed in the superform/plugins folder.")
        client_secret = None

    return_url = 'http://localhost:5000/configure/linkedin'

    authentication = linkedin.LinkedInAuthentication(
        client_id,
        client_secret,
        return_url,
        linkedin.PERMISSIONS.enums.values()
    )
    return authentication


def linkedin_code_processing(code):
    """
    Use the authorization token to generate the access token
    :param code: the authorization_code gotten from the api
    :return: the access token
    """
    authentication = get_linkedin_authentication()
    authentication.authorization_code = code
    access_token = get_access_token(authentication)
    if access_token is not None:
        print("Access Token:", access_token.access_token)
        print("Expires in (seconds):", access_token.expires_in)
        return access_token
    return None


def get_access_token(authentication):
    """
    :param authentication: the access to the LinkedIn account
    :return: the access token linked to the LK account
    """
    try:
        access_token = authentication.get_access_token()
        return access_token
    except linkedin.LinkedInError as err:
        print("A fault occurred while getting the access token")
        traceback.print_exc()
        return None


######################
## post publication ##
######################

def run(publishing, channel_config):
    """ Gathers the informations in the config column and launches the
    posting process """
    json_data = json.loads(channel_config)
    token = json_data['token']
    title = publishing.title
    body = publishing.description  # a quoi tu sers?
    link = publishing.link_url

    comment = title + "\n" + body + "\n" + link
    print("Body: ", body)
    print("Title: ", title)
    print("Link: ", link)

    posted = post(token, comment = comment, title = None, description = None,
                  submitted_url = None, submitted_image_url = None)
    if posted is not None:
        print("Post successful")
    else:
        print("The post failed")


def post(access_token, comment = None, title = None, description = None,
         submitted_url = None, submitted_image_url = None,
         visibility_code = 'anyone'):
    """
    Publishes the post using the python3-linkedin API
    :param access_token: the access token which allows publishing
    :param comment: the body of the article
    :param title: the title of the related image or link
    :param description:
    :param submitted_url: the link
    :param submitted_image_url: the image
    :param visibility_code: visibility of the post on LinkedIn (on
    'anyone' by default
    :return: returns the link to the post just created or an exception
    """
    import collections
    AccessToken = collections.namedtuple('AccessToken',
                                         ['access_token', 'expires_in'])
    authentication = get_linkedin_authentication()
    authentication.token = AccessToken(access_token, "99999999")
    application = linkedin.LinkedInApplication(authentication)
    profile = application.get_profile()
    print("User Profile", profile)
    try:
        resp = application.submit_share(comment, title, description,
                                        submitted_url, submitted_image_url,
                                        visibility_code)
        return resp
    except Exception as e:
        print(e)
        return False


#########################
## credentials reading ##
#########################


def get_linkedin_ini():
    """
    Gets and reads the linkedin.ini file in the plugins folder. Raises an
    exception if the file isn't found
    :return: the config_parser object reading the file
    """
    data_folder = Path("superform/plugins")
    file_to_open = data_folder / "lindekin.ini"
    if not data_folder.is_dir():
        raise FileNotFoundError("Directory not found at %s" % data_folder)
    else:
        if not file_to_open.is_file():
            raise FileNotFoundError("File not found: at %s" % file_to_open)
        else:
            config_parser = configparser.ConfigParser()
            config_parser.read(file_to_open)
            return config_parser


def get_client_id():
    """
    Returns the client_id found in the linekedin.ini file. Raises an exception
    if the linkedin.ini file is not found.
    :return: the client id value found in the linkedin.ini file
    """

    config = get_linkedin_ini()
    c_id = config.get('Credentials', 'CLIENT_ID')
    return c_id


def get_client_secret():
    config = get_linkedin_ini()
    c_secret = config.get('Credentials', 'CLIENT_SECRET')
    return c_secret


#####################
## other functions ##
#####################

def id_generator(size = 6, chars = string.ascii_uppercase + string.digits):
    """
    Generate a random string of 6 characters
    :param size: size
    :param chars: the type of characters (here uppercase and digits)
    :return: string
    """
    return ''.join(random.choice(chars) for _ in range(size))