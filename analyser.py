import os
from os_reader import OSReader
import csv
import openai
import xlsxwriter
from collections import defaultdict


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
        self.functions = self._get_all_functions()
        self.logs = defaultdict(list)

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
                if any(function in row[4] for function in self.functions) or any(function in row[3] for function in self.functions) or "json" in row[4]:
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

        self._write_to_worksheet(unanswered_worksheet, fields, unanswered_rows)
        self._write_to_worksheet(nonsensical_worksheet, fields, nonsensical_rows)
        self._write_to_worksheet(probe_worksheet, probe_rows, probe_rows)

        workbook.close()

    @staticmethod
    def _get_all_functions():
        with open("functions.txt", mode="r") as f:
            file_content = f.read()

        functions = [function.strip() for function in file_content.split(",")]

        return functions

    @staticmethod
    def _write_to_worksheet(worksheet, fields, rows):
        worksheet.write_row(0, 0, fields)

        for i, row in enumerate(rows, start=1):
            worksheet.write_row(i, 0, row)