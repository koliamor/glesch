import sys
import argparse
import xml.etree.ElementTree as ET


def show_comp(comp):
    print('\n')
    print('Components: %d' % len(comp))
    for element in comp:
        print('ID: %s, Name: %s' % (element[4].text, element))


def show_imgs(imgs):
    print('\n')
    print('Images: %d' % len(imgs))
    for element in imgs:
        print(element[0].text)


def find_imge(element, imgname):
    # Найти все элементы включая вложения
    imgobj = element.findall('.//ImageName')
    for element in imgobj:
        if element.text == imgname:
            return True
    return False


def createParser():
    parser = argparse.ArgumentParser(
        prog = 'glesch',
        description = '''Gluing schemes for Rapid SCADA''',
        epilog = '''Copyright (c) koliamor 2019. 
        Licensed under the Apache License, Version 2.0''')
    parser.add_argument('-fo', nargs='?', default='GleSchOut.sch',
        help = 'Output file', metavar = 'OUT FILE')
    parser.add_argument('-fi', nargs='+', default=[],
        help = 'Input file(s)', metavar = 'IN FILES')
    parser.add_argument('-dni', action='store_const', const=True,
        help = 'Delete unused images', metavar = 'DEL NU IMG')
    subparsers = parser.add_subparsers(dest='command')
    delete_parser = subparsers.add_parser('delete',
        help = 'Delete objects including specified images from files',
        description = 'Delete objects including specified images from files')
    delete_parser.add_argument('-di', nargs='+', default=[],
        help = 'Images for delete in files', metavar = 'DEL IMG')
    delete_parser.add_argument('-df', nargs='+', default=[],
        help = 'Files for delete images', metavar = 'DEL FILE')
    return parser


# Загрузка параметров из командной строки
if __name__ == '__main__':
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])
    # print(namespace)

# Проверка на наличие входных файлов
if len(namespace.fi) == 0:
    print('Error: No input files')
    raise SystemExit(1)

# Удалить неиспользуемые изображения
DelNuImgs = namespace.dni

# Удалить указанные объекты изображений из файлов
ImgObjDel = False   # Удалить объекты с изображениями
ImgForDel = []      # Cписок изображения для удаления объектов
ImgDelAll = False   # Удилить во всех файлах
FlsForDel = []      # Cписок файлов для удаления объектов
if namespace.command == 'delete':
    ImgForDel = namespace.di
    FlsForDel = namespace.df
    if len(namespace.di) > 0:
        ImgObjDel = True
    if (len(namespace.df) == 1) and (namespace.df[0] == 'all'):
        ImgDelAll = True


# Файлы
FileOut = namespace.fo  # Выходной файл
Files = namespace.fi    # Файлы для слияния
NumFiles = len(Files)   # Кол-во файлов
CmpName = ['Scheme', 'Components', 'Images', 'CnlsFilter']

Components = []  # Все компоненты
Images = []  # Все изображения

# Извлечение данных из файлов
for i in range(NumFiles):
    tree = ET.parse(Files[i])
    root = tree.getroot()
    # Проверка файлов
    RetVal = 0
    if len(root) != 4:
        RetVal = 10
    if RetVal == 0 and root.tag != 'SchemeView':
        RetVal = 11
    if RetVal == 0:
        for element in root:
            if CmpName.count(element.tag) == 0:
                RetVal = 12
    if RetVal > 0:
        print('Error: In input file structure %s, code: %d' %
              (Files[i], RetVal))
        raise SystemExit(RetVal)

    comp = root[1]  # Копия компонентов
    imgs = root[2]  # Копия изображений

    for element in comp:  # Извлечение компонентов
        # print(element)
        if not ImgObjDel:  # Обычное копирование компонента
            Components.append(element)
        else:  # Удаляются указанные изображения из указанных файлов
            file = Files[i]
            imgDelete = False
            if ImgDelAll or (file in FlsForDel):
                for imgname in ImgForDel:
                    if find_imge(element, imgname):
                        imgDelete = True
            if not imgDelete:  # Копирование компонента
                Components.append(element)

    for element in imgs:  # Извлечение изображений
        # print(element)
        Images.append(element)

# show_comp(Components)
# show_imgs(Images)


# Исправление нумерации компонентов
IdNum = 1
for element in Components:
    element[4].text = str(IdNum)
    IdNum = IdNum + 1


# Удаление дубликатов изображений
ImgsName = []  # Список имен фйлов изображений
NewImages = []  # Список изображений без дубликатов
for element in Images:
    ImgsName.append(element[0].text)  # Получить список имен файлов
# print(ImgsName)
ImgsName = list(set(ImgsName))  # Удалить дубликаты из списка
ImgsName.sort()  # Сортировка списка

# Удалить неиспользуемые изображения
if DelNuImgs:
    newImgs = []
    for imgname in ImgsName:
        imgFind = False
        # print(imgname)
        for element in Components:
            if find_imge(element, imgname):
                imgFind = True
                break
        if imgFind:
            newImgs.append(imgname)
        # else: print("dni: %s" % imgname)
    ImgsName = newImgs

# Создать новый список без дубликатов
for imgname in ImgsName:
    for element in Images:
        if imgname == element[0].text:
            NewImages.append(element)
            break

# show_comp(Components)
# show_imgs(NewImages)


# Создание нового файла
tree = ET.parse(Files[0])   # За основу берется первый файл
root = tree.getroot()

while len(root[1]) > 0:     # Удаление компонентов
    # print(root[1][0])
    root[1].remove(root[1][0])
while len(root[2]) > 0:     # Удаление изображений
    # print(root[2][0])
    root[2].remove(root[2][0])
for element in Components:  # Добавление новых компонентов
    root[1].append(element)
for element in NewImages:   # Добавление новых изображений
    root[2].append(element)

# Формат тегов "Основых" компонентов
UrnStr = "{urn:rapidscada:scheme:basic}"
MainComp = False
for element in root[1]:
    # print(element)
    i = (str(element.tag)).find(UrnStr)
    if i != -1:
        MainComp = True
        # print(i)
        string = str(element.tag)
        element.tag = "basic:" + string[len(UrnStr):len(string)]

# Если используются "Основные" компоненты следует добавить атрибут в заголовок
if MainComp:
    root.set('xmlns:basic', 'urn:rapidscada:scheme:basic')

# Вывод документа в файл
tree = ET.ElementTree(root)
with open(FileOut, "wb") as fh:
    tree.write(fh, encoding='utf-8', xml_declaration=True)
