import fnmatch
import os


class OSReader:
    def __init__(self):
        self.files = {}
        count = 1
        for file in os.listdir("."):
            if fnmatch.fnmatch(file, "*.csv"):
                self.files[count] = file
                count += 1

    def list_all_files(self):
        print("---------------Listing all files---------------")
        for i, name in self.files.items():
            print(f"{i}. {name}")

    def choose_file(self):
        print("---------------Choose a file---------------")
        try:
            file_number = int(input("Enter number of a file to analyse:"))
        except:
            print("Please enter a valid number of a file")

        return self.files[file_number]