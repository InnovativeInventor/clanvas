import collections
import json
import os
import shutil

import google.auth
import requests
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import client, file, tools  # deprecated


# Used https://developers.google.com/classroom/quickstart/python as a refrence
class Gclass:
    def __init__(self, creds_file):
        """
        First setup up something using file_auth or connect_auth.
        """
        self.creds_file = creds_file
        self.service = None
        self.creds = None
        self.courses = None
        self.scopes = None
        self.client_id = None
        self.client_secret = None
        self.hostname = None

    def __add__(self, other):
        """
        TODO: Test
        Intended to be used for admins to be able to view all classes, assignments, etc.
        """
        self.courses.extend(other.courses)
        return self.courses

    # def __str__(self):
    # return

    def file_auth(self, token):
        """
        Authenticates using a given file
        """
        if not os.path.isfile(token):
            raise FileNotFoundError(token + " not found.")

        store = file.Storage(token)
        creds = store.get()
        if creds.invalid:
            raise GclassCredInvalidError("File given is invalid!")
        else:
            self.creds = creds
        self.build()

    def setup_auth(
            self,
            token,
            scopes=[
                'https://www.googleapis.com/auth/classroom.courses.readonly',
                'https://www.googleapis.com/auth/classroom.coursework.me.readonly'
            ]):
        """
        Sets up oauth. Filename is usually creds.json.
        Default scopes are ['https://www.googleapis.com/auth/classroom.courses.readonly', 'https://www.googleapis.com/auth/classroom.coursework.me.readonly']
        Make sure that the proper token is called (don't want to overwrite someone else's token file)
        """
        try:
            self.fileAuth(token)
            return
        except FileNotFoundError:
            pass
        except GclassCredInvalidError:
            os.remove(token)  # Might not be necessary
            pass

        self.combineScopes(scopes)
        token = file.Storage(token)
        creds = token.get()
        flow = client.flow_from_clientsecrets(self.creds_file, self.scopes)
        creds = tools.run_flow(flow, token)
        self.creds = creds
        self.build()

    def auth(token_string):
        pass

    def cred_import(filename: str):
        with open(filename, 'r') as cred_file:
            cred_data = json.load(cred_file)
        self.client_id = cred_data['installed']['client_id']
        self.client_secret = cred_data['installed']['client_secret']

    def combineScopes(self, scopes):
        """
        Combines scopes and checks if they are valid, function websites with proper responses.
        TODO: Implement caching to prevent quering the server too many times
        """
        try:
            for scope in scopes:
                requests.get(scope, timeout=3)
        except:  # Should be more specific TODO: Check if this hides request.get's errors.
            raise GclassScopeError("Scope does not work")

        SCOPES = " ".join(scopes)
        self.scopes = SCOPES

        return SCOPES

    def build(self):
        if not self.creds:
            raise ValueError("self.creds is nonexistent!")

        if self.creds.invalid:
            raise GclassCredInvalidError("File given is invalid!")

        self.service = build(
            'classroom', 'v1', http=self.creds.authorize(Http()))

    def printCourses(self, limit=100):
        self.getCoursesList(pageSize=limit)
        if self.courses is not []:
            for course in self.courses:
                print(course['name'])
        else:
            raise ValueError("No courses to display")

    def printCoursesId(self, limit=100):
        self.getCoursesList(pageSize=limit)
        if self.courses is not []:
            for course in self.courses:
                print(course['name'] + ": " + course['id'])
        else:
            raise ValueError("No courses to display")

    def getCoursesList(self, pageSize=100):
        """
        Returns all names of courses
        """
        results = self.service.courses().list(pageSize=pageSize).execute()
        self.courses = results.get('courses', [])
        if not self.courses:
            return []
        return self.courses  # Might not have to return self.courses, but it's useful for now

    def printAssignmentsList(self,
                             limit=100,
                             fallback_size=(158, 43),
                             symbol="-"):
        """
        Prints all assignments in all courses
        Fallback_size: the screen size, if not running in a window
        Symbol: the symbol to repeat to seperate each assignment
        """
        assignments_list = self.getAssignmentsList(limit=100)
        if not isinstance(assignments_list, collections.Iterable
                          ):  # This should (hopefully) never be the case
            raise ValueError(
                "Type list was expeted for variable \"assignments_list\" but got: \n"
                + assignments_list)

        for i, each_assignment in enumerate(assignments_list):
            (columns, _) = shutil.get_terminal_size(fallback=fallback_size)
            if isinstance(each_assignment, collections.Mapping):
                if each_assignment['courseId']:
                    print(each_assignment['courseId'])
                if each_assignment['title']:
                    print(each_assignment['title'])
                if 'dueDate' in each_assignment:
                    print(
                        str(each_assignment['dueDate']['month']) + "-" +
                        str(each_assignment['dueDate']['day']) + "-" +
                        str(each_assignment['dueDate']['year']))
                print()
                if each_assignment['description']:
                    print(each_assignment['description'])
                if each_assignment['alternateLink']:
                    print(each_assignment['alternateLink'])

                if len(assignments_list) is not i + 1:
                    print()  # Probably a better way to do this
                    if not isinstance(symbol, str):
                        raise TypeError("Symbol needs to be type string!")
                    print(symbol * columns)
                    print()

            else:  # This should (hopefully) never be the case
                raise ValueError(
                    "Type dict was expeted for variable \"each_assignment\" but got: \n"
                    + each_assignment)

    def getAssignmentsList(self, limit=100):
        """
        Returns list of all assignments in all courses
        TODO: actually implement limits
        """
        assignments_list = []

        if self.courses:
            for each_course in self.courses:
                id = each_course['id'].rstrip()  # might not need rstrip
                # name = each_course['name']
                class_assignments = self.getCourseAssignments(id)
                assignments_list.extend(class_assignments)
            return assignments_list
        else:
            self.getCoursesList()
            return self.getAssignmentsList()

    def getCourseAssignments(self, id, limit=100):
        """
        Returns a list of all the assignments in one course
        """
        results = self.service.courses().courseWork().list(
            courseId=id, pageSize=limit).execute()
        assignments = results.get('courseWork', [])
        return assignments


class Error(Exception):
    """
    Base class for exceptions in this module.
    """
    pass


class GclassCredInvalidError(Error):
    """
    For all credential invalid errors
    """

    def __init__(self, message):
        self.message = message


class GclassScopeError(Error):
    """
    For all scope errors.
    """

    def __init__(self, message):
        self.message = message

