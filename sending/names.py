import cyrtranslit
from difflib import SequenceMatcher

names = open("names.txt", "r", encoding="cp1251").readlines()
names = [x.strip() for x in names]


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def get_name(line: str):
    words = line.split(" ")
    cyr_words = [cyrtranslit.to_cyrillic(word, "ru") for word in words]
    cyr_words = [x.strip().lower() for x in cyr_words]
    scores = []
    for name in names:
        score = max([similar(input_word, name) for input_word in cyr_words])
        scores.append(score)

    max_score = max(scores)
    if max_score > 0.85:
        return names[scores.index(max(scores))].capitalize()
