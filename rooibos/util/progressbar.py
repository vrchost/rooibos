import time
import sys


class ProgressBar:

    _day = 3600 * 24
    _hour = 3600
    _min = 60

    def __init__(self, total, width=79, arrowchar='>', completedchar='=',
                 remainingchar='-', mindelay=0.5):
        self.starttime = [(time.time(), 0)] * 10
        self.total = total
        self.width = width
        self.arrowchar = arrowchar
        self.completedchar = completedchar
        self.remainingchar = remainingchar
        self.lastupdate = 0.0
        self.mindelay = mindelay

    def update(self, current, force=False):
        now = time.time()
        if (not force and now - self.lastupdate <= self.mindelay) or \
                self.total == 0:
            return
        self.lastupdate = now
        remainingtime = ''
        if current > 0 and current < self.total:
            elapsedtime = now - self.starttime[0][0]
            elapseditems = current - self.starttime[0][1]
            if elapseditems > 0:
                if elapsedtime > 5:
                    del self.starttime[0]
                    self.starttime.append((now, current))
                r = int(
                    elapsedtime / elapseditems * (self.total - current)) + 1
                if r > ProgressBar._day:
                    remainingtime = ' %dd%02dh' % (
                        r / ProgressBar._day,
                        r % ProgressBar._day / ProgressBar._hour
                    )
                elif r > ProgressBar._hour:
                    remainingtime = ' %dh%02dm' % (
                        r / ProgressBar._hour,
                        r % ProgressBar._hour / ProgressBar._min
                    )
                elif r > ProgressBar._min:
                    remainingtime = ' %dm%02ds' % (
                        r / ProgressBar._min,
                        r % ProgressBar._min
                    )
                elif r > 0:
                    remainingtime = ' %ds' % r
        percent = int(current * 100 / self.total)
        barlength = self.width - len(str(current)) - len(str(self.total)) - \
            len(str(percent)) - len(remainingtime) - 4
        if percent >= 100:
            self.arrowchar = ''
        completed = int(barlength * percent / 100)
        remaining = int(barlength - completed - 1)
        sys.stdout.write("%s/%s %s%s%s %s%%%s\r" % (
            current,
            self.total,
            self.completedchar * completed,
            self.arrowchar,
            self.remainingchar * remaining,
            percent,
            remainingtime
        ))
        sys.stdout.flush()

    def done(self):
        self.update(self.total, force=True)
        print()


if __name__ == "__main__":
    pb = ProgressBar(1234, completedchar='*', remainingchar='~')
    for i in range(1235):
        pb.update(i)
        if i < 10 or (i > 500 and i < 510):
            time.sleep(0.5)
        time.sleep(0.006)
    pb.done()
