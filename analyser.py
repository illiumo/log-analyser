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
        self.functions = self._get_all_functions()

    def start(self):
        self.reader.list_all_files()
        file = self.reader.choose_file()

        fields = []
        all_rows = []
        unanswered_rows = []
        nonsensical_rows = []
        probe_rows = []

        with open(file, mode="r", encoding="utf-8-sig") as csvfile:
            csvreader = csv.reader(csvfile, delimiter=",")

            fields = next(csvreader)

            for row in csvreader:
                all_rows.append(row)
                if any(function in row[4] for function in self.functions) or \
                        any(function in row[3] for function in self.functions) or \
                                "json" in row[4]:
                    probe_rows.append(row)
                elif any(phrase in row[4] for phrase in self.unanswered_phrases):
                    completion = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "developer", "content": "You are a classifier to identify inappropriate or nonsensical questions. " +
                                                                "Classify as nonsensical (1) ONLY if the question is: inappropriate, sexual, offensive, spam, " +
                                                                "test questions ('test', 'hello', 'who are you'), random gibberish, questions about the AI system itself, " +
                                                                "or completely unrelated to any reasonable service inquiry. " +
                                                                "Examples of nonsensical: 'where can I swim naked', 'who are you', 'test', 'hello', random single words. " +
                                                                "Classify as reasonable (0) for ANY legitimate question about travel, services, locations, weather, " +
                                                                "reservations, activities, information requests, or business inquiries - even if oddly phrased. " +
                                                                "Information hidden by ***** represents sensitive location data. " +
                                                                "When in doubt, classify as reasonable (0). Return only 1 or 0."},
                            {"role": "user", "content": row[3]}
                        ]
                    )

                    result = completion.choices[0].message.content

                    if result == "1":
                        nonsensical_rows.append(row)
                    elif result == "0":
                        unanswered_rows.append(row)

        workbook = xlsxwriter.Workbook(os.path.splitext(os.path.basename(file))[0] + ".xlsx")

        unprocessed_worksheet = workbook.add_worksheet("Unprocessed")
        unanswered_worksheet = workbook.add_worksheet("Unanswered")
        nonsensical_worksheet = workbook.add_worksheet("Nonsensical")
        probe_worksheet = workbook.add_worksheet("Probe")

        self._write_to_worksheet(unprocessed_worksheet, fields, all_rows)
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