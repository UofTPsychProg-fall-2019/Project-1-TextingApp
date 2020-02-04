from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
from kivy.storage.dictstore import DictStore
from time import time
import random
import string
import csv
from os import path

### practice and trial phrases, along with phrase ids, for this one participant
PHRASES = [
    {"id": "P1", "text": "i'll be there in 5 minutes", "practice": True},
    {"id": "P2", "text": "i just passed the store", "practice": True},
    {"id": "P3", "text": "let's hang out today", "practice": True},
    {"id": "1", "text": "i'm driving and texting", "practice": False},
    {"id": "2", "text": "do we have milk?", "practice": False},
]

def csvEscape(cell):
    return '"' + str(cell if cell != None else '').replace('"', '""').replace('\n', '\\n') + '"'

def arrayToCsvRow(columns):
    return ','.join(map(csvEscape, columns))

def arrayOfArraysToCsv(rows):
    result = ''
    for row in rows:
        result += arrayToCsvRow(row) + '\n'
    return result

def arrayOfObjectsToCsv(objects):
    keys = set()
    for object in objects:
        for key in object.keys():
            keys.add(key)
    header = list(keys)
    arrayOfArrays = list(map(lambda object: list(map(lambda key: object[key] if key in object else None, header)), objects))
    return arrayToCsvRow(header) + '\n' + arrayOfArraysToCsv(arrayOfArrays)

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))
#identifies trial using random string

class PtcpWin(Screen):
    ptcpid = ObjectProperty(None)

    def btn(self):
        sm.test_index = 0
        sm.curr_ptcp_id = self.ptcpid.text
        #creating a button method which we can bind to the instance of someone pressing "Submit"- it will return their text input
        self.ptcpid.text = ""
        #clears the field once button is pressed

class InstructWin(Screen):
    def btn(self):
        if sm.test_index < len(PHRASES):
            app.root.current = "Test"
            phrase = PHRASES[sm.test_index]
            #if there are test phrases left, label & identify this as a test trial

            test_win = app.root.children[0]
            test_win.ids.phrase_label.text = phrase['text']
            test_win.ids.phrase_input.text = ""
            #set up trial text but leave blank for now

            sm.curr_test_id = randomString()
            sm.curr_phrase_id = phrase['id']
            sm.test_start()
            #at start of current trial, assign random string for "test_id" and assign pre-set phrase # for "phrase_id"

class TestWin(Screen):
    label_id = ObjectProperty(None)

    def text(self, value):
        sm.test_data(value)

    def btn(self):
        sm.test_end()

        if sm.test_index < len(PHRASES):
            app.root.current = "Instructions"
            phrase = PHRASES[sm.test_index]
            #launch instructions screen, and pull phrases

            if not phrase['practice']:
                app.root.current = "Instructions"
                phrase = PHRASES[sm.test_index]
                #pass
                #app.root.current = "Test"
                #if the next trial is a nonpractice phrase, qeue pre-trial Instruction screen
                #non practice intrusctions
        else:
            # finished all tests, take me to done screen
            app.root.current = "Done"

class LastWin(Screen):
    pass

storage = DictStore('data.csv', [])

#create class which reps transitions between the windows
class WindowManager(ScreenManager):
    test_index = 0
    tests = storage.get('data')['data'] if storage.exists('data') else []
    curr_ptcp_id = None
    curr_test_id = None
    curr_phrase_id = None

    def test_start(self):
        self.tests.append([])
        self.test_data("")
        sm.test_index += 1

#define method "test_data" Which will include all variables of interest
    def test_data(self, text):
        if len(self.tests) > 0:
            self.tests[-1].append({
                "ptcp_id": self.curr_ptcp_id,
                "test_id": self.curr_test_id,
                "phrase_id": self.curr_phrase_id,
                "time": time(),
                "text": text
            })

    def test_end(self):
        outputFileName = 'data' + 'ptcp' + self.curr_ptcp_id + '.csv'

        if not path.exists(outputFileName):
            outputFile = open(outputFileName, 'x')
            outputFile.write("ptcp_ID, trial_ID, phrase_ID, time(s), rel_time(s), text, rel_text\n")
        else:
            outputFile = open(outputFileName, 'a')

        writer = csv.writer(outputFile)
        rowlist = []

        self.test_data("")
        last_test = self.tests[-1]
        for i in range(len(last_test)):
            entry = last_test[i]

            if i == 0:
                entry['relative_time'] = 0
            else:
                first_entry = last_test[0]
                entry['relative_time'] = entry['time'] - first_entry['time']

            entry['relative_text'] = ''
            if i > 0:
                prev_entry = last_test[i - 1]
                if len(entry['text']) - 1 == len(prev_entry['text']) and entry['text'][:-1] == prev_entry['text']:
                    entry['relative_text'] = entry['text'][-1]
            rowlist.append([entry['ptcp_id'], entry['test_id'], entry['phrase_id'], entry['time'], entry['relative_time'], entry['text'], entry['relative_text']])
        storage.put('data', data=self.tests)
        self.curr_test_id = None
        self.curr_phrase_id = None
        print("test_end", last_test)
        #write to csv

        #print(rowlist)
        writer.writerows(rowlist)


kv = Builder.load_file("my.kv")
#can now link to kv file even if it breaks naming convention

#create new instance of sm, and that's what we return in our build app
sm = WindowManager()


#so can change screens through the code without having to go into kv file
screens = [PtcpWin(name="PtcpID"), InstructWin(name="Instructions"),TestWin(name="Test"), LastWin(name="Done")]
for screen in screens:
    sm.add_widget(screen)

#create the app class
class MyMainApp(App):
    def build(self):
        return sm

if __name__ == "__main__":
    app = MyMainApp()
    app.run()
