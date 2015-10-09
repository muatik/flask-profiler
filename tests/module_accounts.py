# -*- coding: utf8 -*-
import unittest
from basetest import BaseTest
from bson.objectid import ObjectId
import arrow
from app.modules.accounts import Accounts


class TestAccount(BaseTest, unittest.TestCase):

    ACCOUNTS = [{
        "id": None,
        "fname": "Mustafa",
        "lname": "Atik",
        "email": "mm@aasscsaccccmm.com",
        "gcmId": "code1",
        "alarms": [
            {
                "location": {
                    "country": "United Kingdom",
                    "state": "",
                    "city": "London",
                    },
                "keywords": [
                    "speaker",
                    "scientist",
                    "developer"
                ]
            }, {
                "location": {
                    "country": "United Kingdom",
                    "state": "",
                    "city": "Manchester",
                    },
                "keywords": [
                    "manager"
                ]
            }
        ]
      }, {
        "id": None,
        "fname": "John",
        "lname": "Smith",
        "email": "jmm@jaasscsaccccmm.com",
        "gcmId": "code2",
        "alarms": [
            {
                "location": {
                    "country": "Ireland",
                    "state": "",
                    "city": "Dublin",
                    },
                "keywords": [
                    "waiter",
                    "repair"
                ]
            }
        ]
      }, {
        "id": None,
        "fname": "George",
        "lname": "Mich",
        "email": "gmm@gaasscsaccccmm.com",
        "gcmId": "code3",
        "alarms": [
            {
                "location": {
                    "country": "United Kingdom",
                    "state": "",
                    "city": "Manchester",
                    },
                "keywords": [
                    "developer"
                ]
            }, {
                "location": {
                    "country": "United Kingdom",
                    "state": "",
                    "city": "London",
                    },
                "keywords": [
                    "manager"
                ]
            }
        ]
      }
    ]

    @classmethod
    def setUpClass(cls):
        cls.accounts = Accounts(cls.config)

    def test_00_insert(self):
        for account in self.ACCOUNTS:
            record = self.accounts.insert(account)
            account['id'] = record['id']
            self.assertIsInstance(record['id'], ObjectId)

    def test_01_getWithoutFilter(self):
        accountsFound = self.accounts.get(filtering={})
        self.assertEqual(accountsFound.count(), len(self.ACCOUNTS))

    def test_02_getOne(self):
        account = self.ACCOUNTS[0]
        accountFound = self.accounts.getOne(account['id'])
        self.assertEqual(account['id'], accountFound['id'])

    def test_0401_getByLocationFilter(self):
        def doFilter(account, count, countWithState):
            location = account["alarms"][0]["location"]
            filtering = {
                "location": {
                    "country": location["country"].upper(),
                    "city": location["city"].lower(),
                }
            }

            accountsFound = self.accounts.get(filtering=filtering)
            self.assertEqual(count, accountsFound.count())

            filtering['location']['state'] = location["state"].upper()
            accountsFound = self.accounts.get(filtering=filtering)
            self.assertEqual(countWithState, accountsFound.count())

        doFilter(self.ACCOUNTS[0], 2, 2)  # 3 london accounts
        doFilter(self.ACCOUNTS[1], 1, 1)  # 1 dublin account, 1 central account

    def test_0402_getByKeywordFilter(self):
        def doFilter(keyword, count):
            filtering = {
                "keyword": [keyword]
            }
            accountsFound = self.accounts.get(filtering=filtering)
            self.assertEqual(count, accountsFound.count())
        doFilter("developer", 2)
        doFilter("scientist", 1)

    def test_0405_getByCombinedFilter(self):
        def doFilter(alarm, keyword, count, x=False):
            location = alarm["location"]
            filtering = {
                "location": {
                    "country": location["country"].upper(),
                    "city": location["city"].lower(),
                },
                "keyword": [keyword]
            }
            accountsFound = self.accounts.get(filtering=filtering)
            self.assertEqual(count, accountsFound.count())

        alarm = self.ACCOUNTS[0]["alarms"][0]
        doFilter(alarm, "developer", 1)  # 1 developer in London
        doFilter(alarm, "waiter", 0)  # 0 waiter in Dublin

        alarm = self.ACCOUNTS[2]["alarms"][0]
        doFilter(alarm, "developer", 1)
        doFilter(alarm, "manager", 1)

    def test_0406_getByGcm(self):
        account = self.ACCOUNTS[1]
        accountFound = self.accounts.getByGcm(account["gcmId"])
        self.assertEqual(account["id"], accountFound["id"])

    def test_0500_insertAlarm(self):
        account = self.ACCOUNTS[1]
        newAlarm = {
            "location": {
                "country": "France",
                "state": "",
                "city": "Paris",
                },
            "keywords": [
                "artist"
            ]
        }

        self.accounts.insertAlarm(account["id"], newAlarm)
        accountsFound = self.accounts.get(filtering=newAlarm)
        self.assertEqual(1, accountsFound.count())

    def test_0600_removeAlarm(self):
        account = self.ACCOUNTS[0]
        alarms = account["alarms"]
        initialAlarmsCount = len(alarms)

        self.accounts.removeAlarm(account["id"], alarms[0])
        account = self.accounts.getOne(account["id"])
        self.assertEqual(initialAlarmsCount - 1, len(account["alarms"]))

    def test_0900_deleteAccount(self):
        account = self.ACCOUNTS[0]
        self.accounts.delete(account["id"])
        accountsFound = self.accounts.get()
        self.assertEqual(len(self.ACCOUNTS) - 1, accountsFound.count())

    def test_0700_starredJob(self):
        account = self.ACCOUNTS[0]
        jobId = ObjectId()

        self.accounts.insertStarredJob(account["id"], jobId)
        account = self.accounts.getOne(account["id"])
        self.assertIn(jobId, account["jobs"]["starred"])

        self.accounts.removeStarredJob(account["id"], jobId)
        account = self.accounts.getOne(account["id"])
        self.assertNotIn(jobId, account["jobs"]["starred"])

unittest.main()
