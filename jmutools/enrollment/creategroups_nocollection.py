MAX_CMDLINE_LEN = 2000

import csv
import urllib2
import subprocess


def get_enrollment(course):
    data = urllib2.urlopen(
        'http://feeds.blackboard.jmu.edu/enrollment_flat.pl?id=%s' % course)
    return [':'.join(line.strip().split('\t')[1:]) for line in data]


def run():
    reader = csv.reader(open('groups.txt', 'rb'))
    for row in reader:
        course = row[0] 
        print course

        def get_cmdline(users, first):
            parameters = [
                '-n %s' % course,
                '-a "%s"' % ','.join(users),
                '--createusers',
                ]
            return (r"python.exe ..\..\rooibos\manage.py managegroup %s" %
                    ' '.join(parameters))

        remaining = get_enrollment(course)
        first = True
        while remaining:
            users, remaining = remaining, []
            cmd = get_cmdline(users, first)
            while len(cmd) > MAX_CMDLINE_LEN:
                half = len(users) / 2
                users, remaining = users[:half], remaining + users[half:]
                cmd = get_cmdline(users, first)

            first = False

            print cmd
            print
            subprocess.call(cmd)
            print

if __name__ == '__main__':
    run()

