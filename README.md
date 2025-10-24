This repository creates a very simply Japanese-English dictionary PSQL db. I created this for my japanse-with-text project that needs to integrate with a dictionary. I thought it would be best to have one available to easily query over SQL, with proper indexing of columns, for the sake of speed. This is built by splitting an xml file into logical Python classes and then using that structure to populate a database using psycopg. I have then made a dump of the db and created a docker image which is deployed on docker hub: https://hub.docker.com/r/helboi4/japanese-dict-db The schema has this type of structure
```
CREATE TABLE entries(
      id INT PRIMARY KEY,
      word_kanji TEXT[],
      word_kana TEXT[]);
CREATE TABLE senses(
      id SERIAL PRIMARY KEY,
      definitions TEXT[],
      extra_info TEXT,
      entry_id INT NOT NULL,
      CONSTRAINT fk_entry_id,
      FOREIGN KEY (entry_id),
      REFERENCES entries(id));
```
Each entry has word_kanji (the dictionary form of the word in kanji - may have variant forms, hence the array), word_kana (the dictionary form of the word in hiragana or katakana - this may also have variant forms). The word will always have word_kana but not necessarily word_kanji. Each word has multiple Senses. Senses indicate different meanings of the word. The definition will give different translations for the current meaning, and extra_info will give any contextual information (e.g. if this Sense is only used in a medical context), it has a foreign key to the Entry that it refers to.I hope this database might be useful for others who are building hobby projects that require some basic Japanese language translation like me.
0 commit commentsComments0 (0)Lock conversationComment
