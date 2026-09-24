# Import necessary libraries
import asyncio
import aiohttp
import time
import json
from bs4 import BeautifulSoup
from bs4.element import ResultSet
# from jntuh.Executables import jntuhresultscraper

# Define a class for scraping JNTUH results
class ResultScraper:
    def __init__(self, roll_number):
        
        # Initialize instance variables
        self.url = "http://results.jntuh.ac.in/resultAction"
        self.roll_number = roll_number
        self.results = {"Details": {}, "Results": {}}
        
        # Exam codes for different semesters
        self.exam_codes = {
            "1-1": ["1959", "1936", "1852", "1804", "1764", "1732", "1700", "1658", "1615", "1572", "1504", "1467", "1430", "1404", "1358", "1323"],
            "1-2": ["1956", "1933", "1856", "1801", "1769", "1730", "1705", "1656", "1620", "1622", "1570", "1503", "1481", "1448", "1435", "1381", "1363", "1356"],
            "2-1": ["1972", "1954", "1918", "1834", "1819", "1772", "1728", "1707", "1671", "1667", "1628", "1610", "1560", "1496", "1449", "1425", "1391"],
            "2-2": ["1970", "1952", "1914", "1838", "1814", "1776", "1725", "1715", "1711", "1663", "1627", "1605", "1565", "1501", "1476", "1447", "1437"],
            "3-1": ["1968","1943","1928","1842","1846","1828","1784","1789","1722","1686","1697","1645","1655","1626","1639","1590","1550","1491","1454"],
            "3-2": ["1965", "1946", "1922", "1847", "1850", "1823", "1827", "1780", "1788", "1719", "1696", "1690", "1682", "1649", "1654", "1625", "1638", "1595", "1555", "1502","1965"],
            "4-1": ["1974", "1949", "1866", "1869", "1858", "1861", "1795", "1762", "1758", "1717", "1695", "1678", "1653", "1644", "1640", "1624", "1585", "1545"],
            "4-2": ["1961", "1962", "1939", "1862", "1865", "1808", "1812", "1794", "1790", "1716", "1698", "1691", "1673", "1677", "1672", "1623", "1600", "1580"]
        }

        #To be implemented after implementing redis server
        # self.examcodes=jntuhresultscraper.exam_codes()

        # GPA conversion table
        self.grades_to_gpa = {'O': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 'C': 5, 'F': 0, 'Ab': 0, '-': 0}
        
        # Payloads for different types of result requests
        self.payloads = ["&etype=r17&result=null&grad=null&type=intgrade&htno=", "&etype=r17&result=gradercrv&grad=null&type=rcrvintgrade&htno="]

    async def fetch_result(self, session, exam_code, payload):
        
        # Prepare the payload for the HTTP POST request
        payloaddata="?degree=btech&examCode="+exam_code+payload+self.roll_number

        # Make the HTTP POST request and print the response text
        async with session.get(self.url+payloaddata) as response:
            responseText = await response.text()
            if "156FU" in responseText:
                print(exam_code)
            return responseText

    def scrape_results(self, semester_code, response):
        
        # Parse the response HTML using BeautifulSoup
        soup = BeautifulSoup(response, "lxml")

        # Get student details
        Details = soup.find_all("table")[0].find_all("tr")
        Htno = Details[0].find_all("td")[1].get_text()
        Name = Details[0].find_all("td")[3].get_text()
        Father_Name = Details[1].find_all("td")[1].get_text()
        College_Code = Details[1].find_all("td")[3].get_text()
        
        # Store student details in the results dictionary
        self.results["Details"]["Htno"]=Htno
        self.results["Details"]["Name"]=Name
        self.results["Details"]["Father_Name"]=Father_Name
        self.results["Details"]["College_Code"]=College_Code
        
        Results = soup.find_all("table")[1].find_all("tr")

        Results_column_names = [content.text for content in Results[0].findAll("b")]
        grade_index = Results_column_names.index("GRADE")
        subject_name_index = Results_column_names.index("SUBJECT NAME")
        subject_code_index = Results_column_names.index("SUBJECT CODE")
        subject_credits_index = Results_column_names.index("CREDITS(C)")

        Results = Results[1:]
        for result_subject in Results:
            subject_name = result_subject.find_all("td")[subject_name_index].get_text()
            subject_code = result_subject.find_all("td")[subject_code_index].get_text()
            subject_grade = result_subject.find_all("td")[grade_index].get_text()
            subject_credits = result_subject.find_all("td")[
                subject_credits_index
            ].get_text()
            if(subject_code in self.results["Results"][semester_code] and 
                    self.results["Results"][semester_code][subject_code]["subject_grade"]!='F' and
                    self.results["Results"][semester_code][subject_code]["subject_grade"]!='Ab' and
                    self.results["Results"][semester_code][subject_code]["subject_grade"]!='-' and
                    self.results["Results"][semester_code][subject_code]["subject_grade"]<subject_grade):
                continue
            
            self.results["Results"][semester_code][subject_code] = {}
            self.results["Results"][semester_code][subject_code]["subject_code"] = subject_code
            self.results["Results"][semester_code][subject_code]["subject_name"] = subject_name
            self.results["Results"][semester_code][subject_code]["subject_grade"] = subject_grade
            self.results["Results"][semester_code][subject_code][
                "subject_credits"
            ] = subject_credits


    def total_grade_calculator(self, code, value):
        total = 0
        credits = 0

        for data in value:
            if 'DETAILS' in data:
                continue

            if value[data]['subject_grade'] in ('F', 'Ab','-'):
                return ""

            total += int(self.grades_to_gpa[value[data]['subject_grade']]) * float(value[data]['subject_credits'])
            credits += float(value[data]['subject_credits'])

        self.results["Results"][code]["total"] = total
        self.results["Results"][code]["credits"] = credits
        self.results["Results"][code]["CGPA"] = "{0:.2f}".format(round(total / credits, 2))


    async def scrape_all_results(self, exam_codes="all"):
        async with aiohttp.ClientSession() as session:
            tasks = {}

            if exam_codes == "all":
                exam_codes = self.exam_codes
                if self.roll_number[4] == "5":
                    del exam_codes["1-1"], exam_codes["1-2"]
            else:
                exam_codes = self.exam_codes

            for exam_code in exam_codes.keys():
                # Create a task for each exam code
                tasks[exam_code] = []
                exam_codes[exam_code].reverse()
                for code in exam_codes[exam_code]:
                    for payload in self.payloads:
                        task = asyncio.ensure_future(self.fetch_result(session, code, payload))
                        tasks[exam_code].append(task)

            # Wait for all the tasks to complete
            for exam_code, exam_tasks in tasks.items():
                self.results["Results"][exam_code] = {}

                for result in await asyncio.gather(*exam_tasks):
                    if "Enter HallTicket Number" not in result:
                        self.scrape_results(exam_code, result)

                if bool(self.results["Results"][exam_code]):
                    self.total_grade_calculator(exam_code, self.results["Results"][exam_code])

        return self.results


    def run(self):
        return asyncio.run(self.scrape_all_results())
