import sys
from pathlib import Path

import sqlite3
import random
import re
from tqdm import tqdm

sqlite_file = "Test.db"

class Markov():
    def __init__(self):
        self.maxlength = 15

        self.conn = sqlite3.connect(sqlite_file)
        self.c = self.conn.cursor()

        statement = ("CREATE TABLE IF NOT EXISTS Words("
                                  "id INTEGER PRIMARY KEY   NOT NULL,"
                                  "word TEXT   UNIQUE       NOT NULL,"
                                  "occurrences INT       NOT NULL)");

        self.c.execute(statement)

        statement = ("CREATE TABLE IF NOT EXISTS WordCouples ("
                  "firstword INTEGER NOT NULL,"
                  "secondword INTEGER NOT NULL,"
                  "occurrences INTEGER NOT NULL,"
                  "FOREIGN KEY (firstword) REFERENCES Words (word),"
                  "FOREIGN KEY (secondword) REFERENCES Words (word),"
                  "PRIMARY KEY (firstword, secondword)"
                  ")")

        self.c.execute(statement)

        statement = ("CREATE TABLE IF NOT EXISTS Users ("
                  "id INTEGER PRIMARY KEY NOT NULL,"
                  "nickname TEXT UNIQUE NOT NULL)")

        self.c.execute(statement)

        statement = ("CREATE TABLE IF NOT EXISTS UserWords ("
                    "userid INTEGER NOT NULL,"
                    "wordid INTEGER NOT NULL,"
                    "occurrences INT NOT NULL,"
                    "FOREIGN KEY (userid) REFERENCES Users (id),"
                    "FOREIGN KEY (wordid) REFERENCES Words (id))"
                    )

        self.c.execute(statement)

        self.conn.commit()

    def AddUser(self, user):
        statement = ("SELECT EXISTS(SELECT 1 FROM Users WHERE UPPER(nickname)=UPPER(\"" + user + "\")")
        self.c.execute(statement)
        exists = self.c.fetchone()[0]

        if exists == 1:
            statement = ("INSERT INTO Users (nickname) VALUES (\"" + user + "\")")

    def AddWord(self, user, word):
        statement = "SELECT EXISTS(SELECT 1 FROM Words WHERE UPPER(word)=UPPER(\"" + word +"\"));";
        self.c.execute(statement)

        exists = self.c.fetchone()[0]

        if exists == 1:
            statement = "UPDATE Words SET OCCURRENCES = OCCURRENCES + 1 WHERE UPPER(word)=UPPER(\"" + word +"\");";
        else:
            statement = "INSERT INTO Words (word, OCCURRENCES) VALUES (\"" + word + "\"," + "1);";

        self.c.execute(statement)
        self.conn.commit()


    def AddWordChain(self, first, second):
        statement = ("SELECT EXISTS(SELECT 1 FROM WordCouples WHERE firstword=(SELECT ID FROM Words WHERE UPPER(word) = UPPER(\"" + first  + "\")) AND secondword =(SELECT ID FROM Words WHERE UPPER(word)=UPPER(\"" + second  + "\")));")
        self.c.execute(statement)

        try:
            exists = self.c.fetchone()[0]
            if exists == 1:
                statement = ("UPDATE WordCouples SET OCCURRENCES = OCCURRENCES + 1 WHERE firstword=(SELECT ID FROM Words WHERE UPPER(word)=UPPER(\"" + first + "\")) AND secondword=(SELECT ID FROM Words WHERE UPPER(word)=UPPER(\"" + second + "\"));")
            else:
                statement = ("INSERT INTO WordCouples (firstword, secondword, occurrences) VALUES ((SELECT ID FROM Words WHERE UPPER(word)=UPPER(\"" + first + "\")), (SELECT ID FROM Words WHERE UPPER(word)=UPPER(\"" + second + "\"))," + "1);")

            self.c.execute(statement)
        except:
            print("---------------------------")
            print("Error adding a word couple!")
            print("First word:", first)
            print("Second word:", second)
            print("---------------------------")
        self.conn.commit()

    def AddMessage(self, user, msg):
        words = self.FormatMessage(msg)

        if len(words) > 1:
            self.AddWord(user, words[0])

            for idx in range(0, len(words) - 1, 1):
                self.AddWord(user, words[idx+1])
                self.AddWordChain(words[idx], words[idx + 1])

    def FormatMessage(self, msg):
        msg = re.sub('[^a-zA-ZåäöÅÄÖ \']', '', msg)
        output = msg.split()

        for idx in range(0, len(output), 1):
            if output[idx] == "":
                output.pop[idx]

        return output

    def GetWordList(self, word):
        statement = ("SELECT Words.word, WordCouples.occurrences FROM WordCouples INNER JOIN Words ON Words.ID=WordCouples.secondword WHERE firstword =(SELECT ID FROM Words WHERE UPPER(word)=UPPER(\"" + word +"\"));")
        self.c.execute(statement)

        output = self.c.fetchall()
        return output

    def GetRandomWord(self):
        statement = "SELECT * FROM Words ORDER BY RANDOM() LIMIT 1";
        self.c.execute(statement)
        return self.c.fetchone()[1]

    def GetStats(self, user):
        statement = "SELECT Words.word UserWords.occurrences FROM Words ORDER BY UserWords.occurrences INNER JOIN UserWords WHERE userid=(SELECT id FROM Users WHERE UPPER(nickname)=UPPER(\""+user + "\"))"
        self.c.execute(statement)

        for row in c:
            print(row[0], row[1])

        return self.c.fetchall()

    def CreateMessage(self):
        word = self.GetRandomWord()
        message = word

        run = True
        counter = 0
        while run and (counter < self.maxlength):
            words = self.GetWordList(word)

            if len(words) == 0:
                break

            total = 0
            for w in words:
                total += w[1]

            rand = random.randint(1, total)

            target = 0
            found = False
            while not found:
                for w in words:
                    target += w[1]
                    if rand <= target:
                        message += " " + w[0]
                        word = w[0]
                        found = True
                        break
            counter += 1

        return message

    def ScanFile(self, filename):
        num_lines = sum(1 for line in open(filename, "r"))

        percent = num_lines // 100
        lines_read = 0

        f = open(filename, "r")

        print("Scanning file...")
        for line in tqdm(range(num_lines)):
            self.AddMessage(filename, f.readline())

            lines_read += 1
            if(lines_read % percent == 0):
                progress = lines_read // percent
                #print(progress,"%")

    def ExportWordList(self, filename):
        f = open(filename, "w")

        statement = ("SELECT occurrences, word FROM Words ORDER BY occurrences DESC")
        self.c.execute(statement)

        print("Exporting list of words to ", filename, "...")
        for row in tqdm(self.c):
            out = row[0], " ", row[1], "\n"
            f.write(str(row[1]) + " " + str(row[0]) + str("\n"))
        print("Export complete!")

    def closeDb(self):
        self.conn.close()

mark = Markov()
mark.CreateMessage()
