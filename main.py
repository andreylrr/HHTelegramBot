import hhrequest as hr
import hhparser_description as hp
import hhparser_key_skills as hk
import hhparser_salary as hs
import sys
import time
import json

# Создаем словарь для хранения окончательных результатов
# парсинга зарплат
d_salary = dict()
d_salary["Junior"] = [0, 0, 0]
d_salary["Middle"] = [0, 0, 0]
d_salary["Senior"] = [0, 0, 0]
d_salary["Unknown"] = [0, 0, 0]

def process_vacancies():
    """
        Функция обработки результатов парсинга технологий
    :return: Словарь с отсортированными результатами
    """
        l_terms = o_hhrequest.process_url(s_url)
        i_number_vacancies += 1
        sys.stdout.write("\r")
        sys.stdout.write(f"Завершена обработка вакансии {i_number_vacancies}")

    print(f'\nВсего вакансий: {i_number_vacancies}\n')
    d_sorted = dict(sorted(d_terms_dictionary.items(), key=lambda x: x[1], reverse=True))
    for key, value in d_sorted.items():
        d_sorted[key] = round((value/i_number_vacancies)*100,2)

    print("10 самых популярных технологий")
    for kye, value in list(d_sorted.items())[:10]:
        print(f'{kye} : [{value}%]')
    print("\n")

    return d_sorted

def process_salaries():
    """
        Функция обработки зарплат, указанных в описании вакансий
    :return: Словарь с зарплатами для категорий Seniour, Middle, Junior и Unknown
    """
    def process_salary(salary):
        """
             Функция обработки списка с зарплатой
        :param salary: элемент списка с зарплатой
        """
        if salary:
            d_salary[salary[0]] = [d_salary[salary[0]][0] + salary[1],
                                   d_salary[salary[0]][1] + salary[2],
                                   d_salary[salary[0]][2] + 1]

    # Заменяем парсер в управляющем классе на парсер зарплат
    o_hhrequest.set_parser(o_pars_salary)
    l_salary = []
    i_number_vacancies = 0
    for s_url in l_urls:
        l_salary.append(o_hhrequest.process_url(s_url))
        sys.stdout.write("\r")
        sys.stdout.write(f"Завершена обработка вакансии {i_number_vacancies}")
        i_number_vacancies += 1

    # Обработка списка зарплат полученных от парсера
    for salary in l_salary:
        process_salary(salary)

    # Вычисляем среднее значение зарплат по разным категориям
    if d_salary['Senior'][2] != 0:
        d_salary["Senior"] = [d_salary['Senior'][0] / d_salary['Senior'][2],
                              d_salary['Senior'][1] / d_salary['Senior'][2]]
    if d_salary['Middle'][2] != 0:
        d_salary["Middle"] = [d_salary['Middle'][0] / d_salary['Middle'][2],
                              d_salary['Middle'][1] / d_salary['Middle'][2]]
    if d_salary['Junior'][2] != 0:
        d_salary["Junior"] = [d_salary['Junior'][0] / d_salary['Junior'][2],
                              d_salary['Junior'][1] / d_salary['Junior'][2]]
    if d_salary['Unknown'][2] != 0:
        d_salary["Unknown"] = [d_salary['Unknown'][0] / d_salary['Unknown'][2],
                               d_salary['Unknown'][1] / d_salary['Unknown'][2]]

    print("Результаты анализа зарплат.")
    for key, value in d_salary.items():
        print(f"Для специалиста уровня {key} : минимальная зарплата - {int(value[0])} и максимальная зарплата - {int(value[1])}")

    return d_salary


def add_skills(sum_skills:dict, skills_to_add:list):
    for s_skill in skills_to_add:
        if s_skill in sum_skills:
            sum_skills[s_skill] += 1
        else:
            sum_skills[s_skill] = 1

def sort_skills(skills:dict) -> dict:
    d_sorted = dict(sorted(skills.items(), key=lambda x: x[1], reverse=True))
    for key, value in d_sorted.items():
        d_sorted[key] = round((value/i_number_vacancies)*100,2)
    return d_sorted

if __name__ == '__main__':

    print("Head Hunter Analysis application.")
    # Задаем начальные значения поиска
    d_terms_dictionary = dict()
    s_url = 'https://api.hh.ru/vacancies?area=#'

    # Запрашимваем строку поиска
    s_search = input("Введите строку поиска:")

    # Создаем парсеры для извлечения информации
    o_pars_description = hp.HHParserDescription()
    o_pars_salary = hs.HHParserSalary()
    o_pars_key_skills = hk.HHParserKeySkills()

    # Загружаем вспомогательные файлы для парсера описаний вакансий
    o_pars_description.load_help_files("ignore_terms.txt","double_terms.txt")

    # Создаем класс для работы с парсерами
    o_hhrequest = hr.HHRequest(o_pars_description)
    o_hhrequest.set_url(s_url)

    # Запрашиваем регион поиска у пользователя
    while True:
        s_region = input("Введите регион поиска:")
        try:
             o_hhrequest.set_region(s_region)
             break
        except ValueError:
            print("Регион не найден.")

    # Передаем строку поиска управляющему классу
    o_hhrequest.set_search_pattern(s_search)

    # Получаем список urls вакансий, удовлетворяющих критерию поиска
    print("Получаем список вакансий...")
    l_urls = o_hhrequest.get_urls_vacancies()

    if not l_urls:
        print("По Вашему запросу вакансий не найдено")
    else:
        i_number_vacancies = 0
        d_description:dict = dict()
        d_key_skills:dict = dict()
        l_salary:list = list()
        for s_url in l_urls:
            j_vacancy = req.get(s_url).json()
            add_skills(d_description, o_pars_description.parse(j_vacancy))
            add_skills(d_key_skills, o_pars_key_skills.parse(j_vacancy))
            l_salary.append(o_pars_salary.parse(j_vacancy))
            i_number_vacancies += 1

        d_skills_sorted = sort_skills(d_key_skills)
        d_skills_description = sort_skills(d_description)

        if input("Сохранить результаты поиска Y/N?") == "Y":
            file_name = "".join(s_search)+"-"+time.strftime("%Y%m%d%H%M", time.localtime())
            with open(file_name+"-Description", "w") as f:
                json.dump(d_description, f)
            with open(file_name+"-KeySkills", "w") as f:
                json.dump(d_key_skills, f)
            with open(file_name+"-Salary", "w") as f:
                json.dump(d_salary, f)
