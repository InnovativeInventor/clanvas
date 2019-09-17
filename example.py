import library.gclass

def main():
    ## Setting up
    test = library.gclass.Gclass("credentials.json")
    test.connectAuth("token.json")
    test.fileAuth("token.json")

    # print(test.getCoursesList())
    # test.printCoursesId()
    # print(test.getCourseAssignments(17609195962))
    test.printAssignmentsList()

if __name__ == "__main__":
    main()
