import os
from os_reader import OSReader
import csv


class Analyser:
    def __init__(self):
        self.reader = OSReader()
        self.negative_phrases = [
            "It seems",
            "I understand",
            "I'm sorry"
        ]

    def analyse(self):
        self.reader.list_all_files()
        file = self.reader.choose_file()

        fields = []
        rows = []

        with open(file, mode="r", encoding="utf-8-sig") as csvfile:
            csvreader = csv.reader(csvfile, delimiter=",")

            fields = next(csvreader)

            for row in csvreader:
                if any(phrase in row[4] for phrase in self.negative_phrases):
                    rows.append(row)

        no_ext_filename = os.path.splitext(file)[0]

        file_to_write = no_ext_filename + "-unanswered.csv"

        with open(file_to_write, mode="w") as csvfile:
            csvwriter = csv.writer(csvfile)

            csvwriter.writerow(fields)
            csvwriter.writerows(rows)
