import xml.etree.ElementTree as ET
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
    for i in range(10):
        entry = entry_tree[i]
        print(str(entry))
        
        kele: list = [keb.text if keb else None for keb in entry.find("k_ele")] if entry.find("k_ele") else []
        rele: list = [reb.text if reb else None for reb in entry.find("r_ele")] if entry.find("r_ele") else []
        
        senses: list[Sense] = []
        for sense in entry.findall("sense"):
            gloss_list: list = [gloss.text if gloss else None for gloss in sense.findall("gloss")]
            s_inf: str | None = sense.find("s_inf").text if sense.find("s_inf") else None
            sense_obj = Sense(definitions = gloss_list, extra_info=s_inf)
            senses.append(sense_obj)

        entry_obj = DictEntry(word_kanji=kele, word_kana=rele, senses=senses)
        entries.append(entry_obj)

extractDictEntries()

print(entries)
