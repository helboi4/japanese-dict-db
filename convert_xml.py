import xml.etree.ElementTree as ET
import sys
import logging
import psycopg
import os
import json
from pydantic import BaseModel

db_settings = {
    "host" : "localhost",
    "dbname" : "dictionary",
    "user" : "postgres",
    "password" : "password",
    "port" : 5432,
    "connect_timeout": 10
}

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("psycopg").setLevel(logging.DEBUG)
log = logging.getLogger(__name__)
tree = ET.parse('JMdict.xml')
root = tree.getroot()

# keb is word with kanji (optional)
# reb is work only with kana
# gloss is the meaning of the word (can be multiple)
# s_inf is further context about the word (optional)

class FailedExtractionException(Exception):
    def __init__(self):
        super()

    def __str__(self):
        return "Could not extract any entries from xml"

class BadXmlException(Exception):
    def __init__(self):
        super()

    def __str__(self):
        return "XML file is corrupted. Could not begin extraction"

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

#turn xml into a list of useful python objects with more coherent names for manipulation
def extract_dict_entries(xml_root: any, start: int = 0, stop: int = 0) -> list[DictEntry]:
    if xml_root is None:
        log.error(str(BadXmlException))
        raise BadXmlException
    entries: list[DictEntry] = []
    entry_tree = xml_root.findall("entry")
    if entry_tree == [] or entry_tree is None:
        log.error("Could not find any entries in xml")
        raise BadXmlException
    stop = stop if stop != 0 else len(entry_tree) 
    for i in range(start, stop):
        entry = entry_tree[i]
        kele: list[str] = [str(keb.text) if keb is not None else "" for keb in entry.find("k_ele").findall("keb")] if entry.find("k_ele") is not None else []
        rele: list[str] = [str(reb.text) if reb is not None else "" for reb in entry.find("r_ele").findall("reb")] if entry.find("r_ele") is not None else [] 
        if kele == [] and rele == []:
            log.debug("Could not find information for entry no. %s", i)
            pass
        senses: list[Sense] = []
        for sense in entry.findall("sense"):
            gloss_list: list[str] = [str(gloss.text) if gloss is not None else "" for gloss in sense.findall("gloss")]
            s_inf: str | None = str(sense.find("s_inf").text) if sense.find("s_inf") is not None else None
            sense_obj = Sense(definitions = gloss_list, extra_info=s_inf)
            senses.append(sense_obj)

        entry_obj = DictEntry(word_kanji=kele, word_kana=rele, senses=senses)
        entries.append(entry_obj)
    if entries == []:
        log.debug(str(FailedExtractionException))
        raise FailedExtractionException
    return entries    

# pretty much only here to test extract_dict_entries
def write_entries_to_json(entries: list[DictEntry]) -> None:
    json_str = json.dumps([entry.model_dump() for entry in entries], ensure_ascii=False, indent=4)
    with open("dict.json", "w") as f:
        f.write(json_str)

def write_to_db(entries: list[DictEntry]) -> bool :
    try:
        with psycopg.connect(**db_settings) as con:
            try:
                with con.cursor() as cur:
                    cur.execute("""
                        DROP TABLE IF EXISTS senses;
                    """)
                    cur.execute("""
                        DROP TABLE IF EXISTS entries;
                    """)
                    cur.execute("""
                        CREATE TABLE entries(
                           id INT PRIMARY KEY,
                           word_kanji TEXT[],
                           word_kana TEXT[]
                        );
                    """)
                    cur.execute("""
                        CREATE TABLE senses(
                            id SERIAL PRIMARY KEY,
                            definitions TEXT[],
                            extra_info TEXT,
                            entry_id INT NOT NULL,
                            CONSTRAINT fk_entry_id
                                FOREIGN KEY (entry_id)
                                REFERENCES entries(id)
                        );
                    """)
                    log.info("Tables created successfully")
            except (psycopg.OperationalError, psycopg.ProgrammingError, TypeError) as e:
                log.error(f"Unable to create tables: {str(e)}")
                return False
            with con.cursor() as cur:
                entries_data = []
                senses_data = []
                i = 1
                for entry in entries:  # Start from 1
                    entries_data.append((i, entry.word_kanji, entry.word_kana))
                    for sense in entry.senses:
                        senses_data.append((sense.definitions, sense.extra_info, i))
                    i += 1
                try:
                    cur.executemany("INSERT INTO entries (id, word_kanji, word_kana) VALUES (%s, %s, %s)", entries_data)
                    cur.executemany("INSERT INTO senses (definitions, extra_info, entry_id) VALUES (%s, %s, %s)", senses_data)
                except (psycopg.DataError, psycopg.IntegrityError, psycopg.ProgrammingError, TypeError) as e:
                    log.debug(f"Entry insertion failed: {str(e)}")
                    return False
            con.commit()
    except psycopg.OperationalError as e:
        log.error(f"Unable to establish db connection: {str(e)}")
        return False
    return True

if __name__ == "__main__":
    try:
        entries = extract_dict_entries(root)
    except (BadXmlException):
        log.error("Aborting due to bad xml")
        sys.exit(1)
    except (FailedExtractionException):
        log.error("Aborting due to failure to extract data from xml")
        sys.exit(1)
    db_write_success: bool = write_to_db(entries)
    if not db_write_success:
        log.error("Failed to write entries to db. Aborting")
    else:
        log.info("Sucessfully wrote entries to db.")
