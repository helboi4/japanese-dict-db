import xml.etree.ElementTree as ET
import os
import json
from pydantic import BaseModel

tree = ET.parse('JMdict.xml')
root = tree.getroot()

# keb is word with kanji (optional)
# reb is work only with kana
# gloss is the meaning of the word (can be multiple)
# s_inf is further context about the word (optional)

class Sense(BaseModel):
    definitions: list[str]
    extra_info: str | None

    def __str__(self):
        return f"{{definitions: {self.definitions}, \n extra_info: {self.extra_info}}}"

class DictEntry(BaseModel): 
    word_kanji: list[str]
    word_kana: list[str]
    senses: list[Sense]

    def __str__(self):
        return f"{{word_kanji: {self.word_kanji}, \n word_kana: {self.word_kana}, \n senses: {str(self.senses)}}}"

entries: list[DictEntry] = []

def extractDictEntries():
    entry_tree = root.findall("entry")
    for i in range(50, 100):
        entry = entry_tree[i]
        kele = entry.find("k_ele")
        """ if(kele is not None):
            print(str(kele))
        
            for keb in entry.find("k_ele"):
                print(str(keb.text)) """
        
        kele: list[str] = [str(keb.text) if keb is not None else "" for keb in entry.find("k_ele").findall("keb")] if entry.find("k_ele") is not None else []
        rele: list[str] = [str(reb.text) if reb is not None else "" for reb in entry.find("r_ele").findall("reb")] if entry.find("r_ele") is not None else []
       
        senses: list[Sense] = []
        for sense in entry.findall("sense"):
            gloss_list: list[str] = [str(gloss.text) if gloss is not None else "" for gloss in sense.findall("gloss")]
            s_inf: str | None = str(sense.find("s_inf").text) if sense.find("s_inf") is not None else None
            sense_obj = Sense(definitions = gloss_list, extra_info=s_inf)
            senses.append(sense_obj)

        entry_obj = DictEntry(word_kanji=kele, word_kana=rele, senses=senses)
        entries.append(entry_obj)

extractDictEntries()

print("感じが印刷できるよ")
json_str = json.dumps([entry.model_dump() for entry in entries], ensure_ascii=False, indent=4)
with open("dict.json", "w") as f:
    f.write(json_str)
