import asyncio
import os
from string import ascii_uppercase

from aiohttp import ClientSession
from PIL import Image
from rapidfuzz import fuzz
import easyocr

DEPTH = 8
START = "\033[1m"
END = "\033[0m"
MOVES = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
EXTENSIONS = {"png", "jpg", "jpeg", "svg"}


def read_image(filename: str) -> list[list[str]]:
    files = [file for file in os.listdir('.') if os.path.isfile(file) and file.split(".")[-1] in EXTENSIONS]
    files.sort(key=lambda file: fuzz.ratio(file, filename), reverse=True)
    print(f"Image processing has started: {files[0]}")

    image = Image.open(files[0])
    height, width = image.height, image.width
    for x in range(width):
        for y in range(height):
            color = image.getpixel((x, y))
            if color != (1, 11, 26, 255):
                image.putpixel((x, y), (255, 255, 255, 255))
    image.save("main.png", dpi=(600, 600))

    reader = easyocr.Reader(lang_list=["en"], gpu=True)
    result = reader.readtext("main.png", detail=0, allowlist=ascii_uppercase, mag_ratio=2.8, min_size=20,
                             paragraph=True, decoder="beamsearch")

    matrix = list()
    for row in result:
        matrix.extend([char for char in row if char in ascii_uppercase])
    matrix = [matrix[index:index + 5] for index in range(0, 25, 5)]
    check_matrix(matrix)

    return matrix


def get_bold(string: str) -> str:
    return f"{START}{string}{END}"


def get_path(word: str, path: list[tuple[int, int]]) -> list[list[str]]:
    matrix = [["." for _ in range(5)] for _ in range(5)]

    for index in range(len(path)):
        i, j = path[index]
        matrix[i][j] = word[index].upper() + f"({index + 1})"

    return matrix


def get_word(matrix: list[list[str]], path: list[tuple[int]]) -> str:
    word = str()

    for i, j in path:
        word += matrix[i][j]

    return word.lower()


def check_matrix(matrix: list[list[str]]) -> None:
    error = "Error! Try another image with a higher resolution."

    assert len(matrix) == 5, error
    for row in matrix:
        assert len(row) == 5, error


def DFS(matrix: list[list[str]], i: int, j: int, path: list[tuple], dictionary: set[str], result: dict) -> None:
    n, m = len(matrix), len(matrix[0])
    current_word = get_word(matrix, path + [(i, j)])

    if current_word in dictionary:
        result[current_word] = path + [(i, j)]

    if len(path) == DEPTH - 1:
        return

    for ii, jj in MOVES:
        ii, jj = ii + i, jj + j
        if 0 <= ii < n and 0 <= jj < m and (ii, jj) not in path:
            DFS(matrix, ii, jj, path + [(i, j)], dictionary, result)


async def check_key(key: str) -> bool:
    async with ClientSession() as session:
        async with session.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{key}") as response:
            return response.status == 200


async def main() -> None:
    with open("words.txt") as file:
        dictionary = set(file.read().split())

    matrix = read_image(str(input("Enter image filename: ")))
    n, m = len(matrix), len(matrix[0])

    results = dict()
    for index_i in range(n):
        for index_j in range(m):
            DFS(matrix, index_i, index_j, list(), dictionary, results)

    keys = list(map(str, sorted(results.keys(), key=len, reverse=True)))
    index, found = 0, 0

    while index < len(keys) and found < 3:
        key = keys[index]
        if await check_key(key):
            print(get_bold(key))
            for row in get_path(key, results[key]):
                for item in range(5):
                    row[item] = row[item].center(5, " ")
                print("".join(row))
            found += 1
        index += 1


if __name__ == "__main__":
    os.system("color")
    asyncio.run(main())
