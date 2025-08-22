import xml.etree.ElementTree as ET

tree = ET.parse('JMdict.xml')
root = tree.getroot()

# keb is word with kanji (optional)
# reb is work only with kana
# gloss is the meaning of the word (can be multiple)
# s_info is further context about the word (optional)

class DictEntry(BaseMo)
