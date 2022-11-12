"""
Split a text using each element of a list as delimiter
"""
import re

REGEX = re.compile("/d")

atext = "1Accrocher le linge2Tailler les haies3Ranger le grenier1Vider les poubelles"
alist = ["1", "2", "3", "1"]
step = [
    "Accrocher le linge",
    "Tailler les haies",
    "Ranger le grenier",
    "Vider les pouvelles",
]
expected_result = [
    ("1", "Accrocher le linge"),
    ("2", "Tailler les haies"),
    ("3", "Ranger le greniers"),
    ("1", "Vider les poubelles"),
]


def split_text(text: str, delimiter: str):
    chunk1, chunk2 = text.split(delimiter, 1)[1]
    return split_text(chunk2, delimiter)


final_alist = []
for i, item in enumerate(alist):
    chunk0, chunk1 = atext.split(item, 1)
    final_alist.append(chunk0)
    atext = chunk1
    if i + 1 == len(alist):
        final_alist.append(chunk1)
    # chunk0, chunk1 = atext.split(item, 1)
    # if i == 0:
    #     final_alist.append(chunk0)
    # else:
    #     chunk1 = atext.split(item, 1)[1]
    #     final_alist.append(chunk1)
    #     print(chunk1)
final_alist = final_alist[1:]
print(expected_result)
print(*zip(alist, final_alist))
