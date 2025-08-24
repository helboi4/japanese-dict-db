import xml.etree.ElementTree as ET
import logging
import psycopg
import os
import json
from pydantic import BaseModel

db_settings = {
    "host" : "localhost",
    "database" : "dictionary",
    "user" : "postgres",
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
    entries: list[DictEntry] = []
    entry_tree = xml_root.findall("entry")
    stop = stop if stop != 0 else len(entry_tree) 
    for i in range(start, stop):
        entry = entry_tree[i]
        kele = entry.find("k_ele")
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
                        DROP TABLE IF EXISTS entries
                    """)
                    cur.execute("""
                        CREATE TABLE entries(
                           id SERIAL PRIMARY KEY,
                           word_kanji VARCHAR(255)[],
                           word_kana VARCHAR(255)[],
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
            except psycopg.OperationalError as e:
                log.error(f"Unable to create tables: {str(e)}")
                return False
        with con.cursor() as cur:
            success_count = 0
            for entry in entries:
                savepoint_name = success_count
                savepoint_name = f"entry_{success_count}"
                try:
                    cur.execute("SAVEPOINT %s", savepoint_name)
                    cur.execute("""
                        INSERT INTO entries (word_kanji, word_kana) VALUES (%s, %s)
                        RETURNING id;
                    """, (entry.word_kanji, entry.word_kana))
                    result = cur.fetchone()
                    entry_id = result[0] if result else None
                    if entry_id is not None:
                        for sense in entry.senses:
                            cur.execute("INSERT INTO senses (definitions, extra_info, entry_id) VALUES (%s, %s, %s)", (sense.definitions, sense.extra_info, entry_id))
                    cur.execute("RELEASE SAVEPOINT %s", savepoint_name)
                    success_count += 1
                except (psycopg.DataError, psycopg.IntegrityError) as e:
                    log.debug(f"Entry {entry.word_kanji}, {entry.word_kana} not inserted: {str(e)}")
                    cur.execute("ROLLBACK TO SAVEPOINT %s", savepoint_name)
                    pass
            con.commit()
    except psycopg.OperationalError as e:
        log.error(f"Unable to establish db connection: {str(e)}")
        return False
    return True

if __name__ == "__main__":
    entries = extract_dict_entries(root)
    success: bool = 


