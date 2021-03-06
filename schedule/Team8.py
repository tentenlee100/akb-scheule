"""
Team 8 schedule and news.

ref:
  * https://toyota-team8.jp/schedule/201809/index.php
"""
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

try:
    from schedule.dataType.Schedule import Schedule
except ImportError:  # for test
    from .dataType.Schedule import Schedule


class Team8(object):
    query_date = datetime.today().strftime("%Y/%m/%d")

    def __init__(self, query_date="", debug=False):
        """Get query date string to datetime type.

        Args:
            query_date: (string) ex. 2018/08/10
        """
        if query_date:
            self.query_date = query_date

        self.is_get_all_event = False   # only today
        if debug:
            self.is_get_all_event = True

        try:
            self.today = datetime.strptime(self.query_date, "%Y/%m/%d")
        except (TypeError, ValueError):
            print("Please check your input date format (ex. 2018/10/10)")

    def get_member(self) -> dict:
        """Get AKB48 Team 8 members


        Returns:
            AKB48 Team 8 member list. ex.
            {
                "北海道": "坂口渚沙",
            }
        """
        url = "https://toyota-team8.jp/schedule/"
        headers = {
            "Cache-Control": "no-cache",
        }

        all_member_list = {}
        with requests.Session() as s:
            r = s.get(url, headers=headers)
            if r.status_code == 200:
                html_block = BeautifulSoup(r.text, 'html.parser')
                optgroups = html_block.find_all('optgroup')
                for optgroup in optgroups:
                    opts = optgroup.find_all('option')
                    for opt in opts:
                        parse_text = opt.get_text().split("　")
                        if len(parse_text) > 1:
                            all_member_list[parse_text[0]] = (
                                parse_text[1].replace(' ', ''))
            else:
                print("Connect to Team 8 website fail.")

        return all_member_list

    def _parse_event(self, html) -> list:
        """Parse HTML string to get basic event list.

        Args:
            html: (string) html page

        Returns:
        """
        member_regx = re.compile(r'.*（(.*)）$')
        html_block = BeautifulSoup(html, 'html.parser')

        date_elements = html_block.find_all('th', 'date')
        event_list = []
        for date_element in date_elements:
            if int(date_element.get_text().split('日')[0]) == self.today.day:
                event_dl_list = date_element.parent.find('td').find_all('dl')
                for event_dl in event_dl_list:
                    event_dl.find("dd", 'mainTitle')
                    title = event_dl.find("dd", 'mainTitle').get_text()
                    event_type = event_dl.find("dt", 'category').find('img')['alt']
                    s = Schedule()
                    s.event_type = event_type
                    space_index = title.find(" ")
                    # 過濾標題都有的日期
                    if space_index > -1:
                        s.title = title[space_index:]
                    else:
                        s.title = title

                    check_start_time_index = title.find(":")
                    # 看能不能拿到開始時間
                    if check_start_time_index > -1:
                        # 查看:前後數否為數字(前1或前2)
                        before2 = title[check_start_time_index - 2:check_start_time_index]
                        before1 = title[check_start_time_index - 1:check_start_time_index]
                        end2 = title[check_start_time_index + 1:check_start_time_index + 3]
                        # print("before2 :{} before1:{}  end2: {}".format(before2, before1, end2))
                        if before2.isdigit() and end2.isdigit():
                            s.start_time = before2 + ":" + end2
                        elif before1.isdigit() and end2.isdigit():
                            s.start_time = "0" + before1 + ":" + end2

                    # handle member string in html text
                    member_match = member_regx.search(title)
                    if member_match and len(member_match.groups()) > 0:
                        member_txt = member_match.group(1)
                        if '代表' in member_txt:
                            member_list = []
                            # remove 'xxx 代表．'
                            for m in member_txt.split('、'):
                                name = m.split('・')
                                if len(name) > 1:
                                    member_list.append(name[1])
                            # -remove

                            s.members = member_list
                    # -handle

                    event_list.append(s)
        return event_list

    def get_schedule(self) -> [Schedule]:
        """Get schedule data from website

        Returns:
            A list of schedule object
        """
        url = "https://toyota-team8.jp/schedule/{}/index.php"
        headers = {
            "Cache-Control": "no-cache",
        }
        payload = {}

        schedule_list = []
        qmonth = f"{self.today.year}{self.today.month:0>2}"
        with requests.Session() as s:
            r = s.get(url.format(qmonth), headers=headers, params=payload)
            if r.status_code == 200:
                schedule_list = self._parse_event(r.text)
            else:
                print("Connect to Team 8 website fail.")

        return schedule_list


if __name__ == '__main__':
    result = Team8(debug=False).get_schedule()
    print(result)
    print(f"total: {len(result)} events")

    all_member_list = Team8().get_member()
    print(all_member_list)
    print(f"total: {len(all_member_list)} 人")
