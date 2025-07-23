import os
from os_reader import OSReader
import csv
import openai
import xlsxwriter


class Analyser:
    def __init__(self):
        self.reader = OSReader()
        self.unanswered_phrases = [
            "It seems",
            "I understand",
            "I'm sorry"
        ]
        self.client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        self.functions = self.get_all_functions()

    def analyse(self):
        self.reader.list_all_files()
        file = self.reader.choose_file()

        fields = []
        unanswered_rows = []
        nonsensical_rows = []
        probe_rows = []

        with open(file, mode="r", encoding="utf-8-sig") as csvfile:
            csvreader = csv.reader(csvfile, delimiter=",")

            fields = next(csvreader)

            for row in csvreader:
                if any(function in row[4] for function in self.functions) or "json" in row[4]:
                    probe_rows.append(row)
                elif any(phrase in row[4] for phrase in self.unanswered_phrases):
                    completion = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "developer", "content": "Classify the following text as normal (0) " +
                                                             "or gibberish/random input/etc (1). Return only 0 or 1, nothing else," +
                                                             " if text is missing return 1"},
                            {"role": "user", "content": row[3]}
                        ]
                    )

                    print(completion.choices[0].message.content)

                    if completion.choices[0].message.content == "0":
                        unanswered_rows.append(row)
                    elif completion.choices[0].message.content == "1":
                        nonsensical_rows.append(row)

        workbook = xlsxwriter.Workbook(os.path.splitext(os.path.basename(file))[0] + ".xlsx")

        unanswered_worksheet = workbook.add_worksheet("Unanswered")
        nonsensical_worksheet = workbook.add_worksheet("Nonsensical")
        probe_worksheet = workbook.add_worksheet("Probe")

        unanswered_worksheet.write_row(0, 0, fields)
        nonsensical_worksheet.write_row(0, 0, fields)
        probe_worksheet.write_row(0, 0, fields)

        for i, row in enumerate(unanswered_rows, start=1):
            unanswered_worksheet.write_row(i, 0, row)

        for i, row in enumerate(nonsensical_rows, start=1):
            nonsensical_worksheet.write_row(i, 0, row)

        for i, row in enumerate(probe_rows, start=1):
            probe_worksheet.write_row(i, 0, row)

        workbook.close()

    @staticmethod
    def get_all_functions():
        with open("functions.txt", mode="r") as f:
            file_content = f.read()

        functions = [function.strip() for function in file_content.split(",")]

        return functions
